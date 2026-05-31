"""
主面板 UI 模块
=============
弹出式历史记录面板，包含搜索栏、存储天数选择、卡片列表。
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QScrollArea, QFrame, QLabel, QPushButton,
    QApplication, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import QPixmap, QFont

from .styles import get_stylesheet


# ── 工具函数 ──────────────────────────────────────────

def format_time(time_str: str) -> str:
    """将 ISO 时间戳转为人类可读的相对时间"""
    try:
        t = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return time_str
    delta = datetime.now() - t
    if delta.days > 0:
        return f"{delta.days}天前" if delta.days <= 30 else t.strftime("%Y-%m-%d")
    seconds = delta.seconds
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60}分钟前"
    return f"{seconds // 3600}小时前"


def truncate_text(text: str, max_len: int = 80) -> str:
    """截断文字到指定长度"""
    if len(text) <= max_len:
        return text
    # 在 max_len 处尝试找空格/标点断句
    cut = text[:max_len]
    return cut + "..."

# ── 卡片组件 ──────────────────────────────────────────

class TextCard(QFrame):
    """文字类型卡片"""
    clicked = Signal(int)
    pin_toggled = Signal(int)
    deleted = Signal(int)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("CardPinned" if record["pinned"] else "Card")
        self.setFixedHeight(70)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self._build_ui()
        self._update_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 6)
        layout.setSpacing(4)

        # 第一行：内容预览
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        if self.record["pinned"]:
            badge = QLabel("[置顶]")
            badge.setObjectName("CardBadge")
            badge.setFixedWidth(40)
            top_row.addWidget(badge)

        content = QLabel(truncate_text(self.record.get("text_content", "")))
        content.setObjectName("CardContent")
        content.setWordWrap(True)
        top_row.addWidget(content, 1)
        layout.addLayout(top_row)

        # 第二行：时间 + 操作按钮
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        time_label = QLabel(format_time(self.record.get("created_at", "")))
        time_label.setObjectName("CardTime")
        bottom_row.addWidget(time_label)

        bottom_row.addStretch()

        # 悬停操作按钮
        self.pin_btn = QPushButton("置顶" if not self.record["pinned"] else "取消")
        self.pin_btn.setObjectName("PinBtn")
        self.pin_btn.setFixedHeight(22)
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.record["id"]))
        self.pin_btn.setVisible(False)
        bottom_row.addWidget(self.pin_btn)

        self.del_btn = QPushButton("删除")
        self.del_btn.setObjectName("DeleteBtn")
        self.del_btn.setFixedHeight(22)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.record["id"]))
        self.del_btn.setVisible(False)
        bottom_row.addWidget(self.del_btn)

        layout.addLayout(bottom_row)

    def _update_style(self):
        self.setObjectName("CardPinned" if self.record["pinned"] else "Card")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.record["id"])
        super().mousePressEvent(event)

    def enterEvent(self, event: QEvent):
        self._hovered = True
        self.pin_btn.setVisible(True)
        self.del_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self._hovered = False
        self.pin_btn.setVisible(False)
        self.del_btn.setVisible(False)
        super().leaveEvent(event)


class ImageCard(QFrame):
    """图片类型卡片"""
    clicked = Signal(int)
    pin_toggled = Signal(int)
    deleted = Signal(int)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("CardPinned" if record["pinned"] else "Card")
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self._build_ui()
        self._update_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 左侧：缩略图
        thumb_label = QLabel()
        thumb_label.setFixedSize(120, 60)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet("background: #F5F5F5; border-radius: 4px;")

        image_path = self.record.get("image_path", "")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                thumb_label.setPixmap(pixmap)
            else:
                thumb_label.setText("[图片]")
        else:
            thumb_label.setText("[图片]")
        layout.addWidget(thumb_label)

        # 右侧：信息区
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        if self.record["pinned"]:
            badge = QLabel("[置顶]")
            badge.setObjectName("CardBadge")
            info_layout.addWidget(badge)

        # 文件大小
        size_str = ""
        image_path = self.record.get("image_path", "")
        if image_path and os.path.exists(image_path):
            size_bytes = os.path.getsize(image_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes // 1024}KB"
            else:
                size_str = f"{size_bytes // (1024*1024)}MB"
        type_label = QLabel(f"图片 · {size_str}" if size_str else "图片")
        type_label.setObjectName("CardContent")
        info_layout.addWidget(type_label)

        time_label = QLabel(format_time(self.record.get("created_at", "")))
        time_label.setObjectName("CardTime")
        info_layout.addWidget(time_label)

        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

        # 操作按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.addStretch()

        self.pin_btn = QPushButton("置顶" if not self.record["pinned"] else "取消")
        self.pin_btn.setObjectName("PinBtn")
        self.pin_btn.setFixedSize(40, 22)
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.record["id"]))
        self.pin_btn.setVisible(False)
        btn_layout.addWidget(self.pin_btn)

        self.del_btn = QPushButton("删除")
        self.del_btn.setObjectName("DeleteBtn")
        self.del_btn.setFixedSize(40, 22)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.record["id"]))
        self.del_btn.setVisible(False)
        btn_layout.addWidget(self.del_btn)

        layout.addLayout(btn_layout)

    def _update_style(self):
        self.setObjectName("CardPinned" if self.record["pinned"] else "Card")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.record["id"])
        super().mousePressEvent(event)

    def enterEvent(self, event: QEvent):
        self._hovered = True
        self.pin_btn.setVisible(True)
        self.del_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self._hovered = False
        self.pin_btn.setVisible(False)
        self.del_btn.setVisible(False)
        super().leaveEvent(event)


# ── 主面板 ────────────────────────────────────────────

class MainWindow(QWidget):
    """剪贴板历史主面板"""

    closed = Signal()  # 面板被隐藏时发射

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.db = database

        self.setObjectName("MainWindow")
        self.setWindowTitle("剪贴板历史")
        self.setFixedSize(400, 560)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Popup
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._build_ui()
        self.setStyleSheet(get_stylesheet())

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ── 标题栏（标题 + 关闭按钮）──
        title_bar = QHBoxLayout()
        title_bar.setSpacing(0)

        title = QLabel("剪贴板历史")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title_bar.addWidget(title)

        title_bar.addStretch()

        close_panel_btn = QPushButton("X")
        close_panel_btn.setFixedSize(26, 26)
        close_panel_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent; border: none;"
            "  color: #999999; font-size: 14px; font-weight: bold;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "  background: #FFE0E0; color: #FF6B6B;"
            "}"
        )
        close_panel_btn.clicked.connect(self.hide)
        title_bar.addWidget(close_panel_btn)

        main_layout.addLayout(title_bar)

        # ── 顶部：搜索 + 保留天数 ──
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("搜索复制的文字...")
        self.search_box.textChanged.connect(self._on_search)
        top_row.addWidget(self.search_box, 1)

        self.retention_box = QComboBox()
        self.retention_box.setObjectName("RetentionBox")
        self.retention_box.addItems(["1天", "3天", "5天"])
        current_days = self.db.get_retention_days()
        day_map = {1: 0, 3: 1, 5: 2}
        self.retention_box.setCurrentIndex(day_map.get(current_days, 1))
        self.retention_box.currentTextChanged.connect(self._on_retention_change)
        top_row.addWidget(self.retention_box)

        main_layout.addLayout(top_row)

        # ── 内容区（卡片列表 或 空状态）──
        self.content_stack = QWidget()  # 占满中间空间
        content_stack_layout = QVBoxLayout(self.content_stack)
        content_stack_layout.setContentsMargins(0, 0, 0, 0)
        content_stack_layout.setSpacing(0)

        # 有记录时：滚动卡片列表
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(6)
        self.card_layout.addStretch()

        self.scroll_area.setWidget(self.card_container)
        content_stack_layout.addWidget(self.scroll_area)

        # 无记录时：空状态引导
        self.empty_state = QWidget()
        self.empty_state.setVisible(False)
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(8)

        # 大图标区域（用背景色 + 文字模拟）
        icon_label = QLabel()
        icon_label.setFixedSize(72, 72)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            "background-color: #E8F4F8;"
            "border: 2px dashed #A8D8EA;"
            "border-radius: 14px;"
            "font-size: 13px;"
            "font-weight: bold;"
            "color: #7EC8E3;"
        )
        icon_label.setText("剪切板")
        empty_layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        hint_text = QLabel("复制文字或图片后会自动显示在这里")
        hint_text.setAlignment(Qt.AlignCenter)
        hint_text.setStyleSheet("color: #9E9E9E; font-size: 12px; padding-top: 6px;")
        empty_layout.addWidget(hint_text)

        shortcut_hint = QLabel("Ctrl+Shift+V 快速打开面板")
        shortcut_hint.setAlignment(Qt.AlignCenter)
        shortcut_hint.setStyleSheet("color: #A8D8EA; font-size: 11px;")
        empty_layout.addWidget(shortcut_hint)

        content_stack_layout.addWidget(self.empty_state)
        main_layout.addWidget(self.content_stack, 1)

        # ── 底部操作栏 ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.count_label = QLabel("共 0 条记录")
        self.count_label.setObjectName("CountLabel")
        bottom_row.addWidget(self.count_label)

        bottom_row.addStretch()

        self.clear_btn = QPushButton("清空全部")
        self.clear_btn.setObjectName("ClearBtn")
        self.clear_btn.clicked.connect(self._on_clear_all)
        bottom_row.addWidget(self.clear_btn)

        exit_btn = QPushButton("退出")
        exit_btn.setObjectName("ClearBtn")  # 复用样式
        exit_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #FFFFFF; border: 1px solid #E0E0E0;"
            "  border-radius: 6px; padding: 6px 14px;"
            "  font-size: 12px; color: #666666;"
            "}"
            "QPushButton:hover {"
            "  background-color: #E8F4F8; border-color: #7EC8E3; color: #5BA4C9;"
            "}"
        )
        exit_btn.clicked.connect(QApplication.quit)
        bottom_row.addWidget(exit_btn)

        main_layout.addLayout(bottom_row)

    # ── 公共方法 ──────────────────────────────────────

    def refresh(self):
        """刷新卡片列表"""
        search = self.search_box.text().strip()
        records = self.db.get_all(search=search)

        # 清空旧卡片
        for i in reversed(range(self.card_layout.count())):
            item = self.card_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        if not records:
            # 切换到空状态
            self.scroll_area.setVisible(False)
            self.empty_state.setVisible(True)
            self.clear_btn.setVisible(False)
            self.count_label.setText("共 0 条记录")
            return

        # 切换到列表状态
        self.scroll_area.setVisible(True)
        self.empty_state.setVisible(False)
        self.clear_btn.setVisible(True)
        self.count_label.setText(f"共 {len(records)} 条记录")

        for rec in records:
            if rec["content_type"] == "text":
                card = TextCard(rec)
            else:
                card = ImageCard(rec)

            card.clicked.connect(self._on_card_clicked)
            card.pin_toggled.connect(self._on_pin_toggle)
            card.deleted.connect(self._on_delete)
            self.card_layout.addWidget(card)

        self.card_layout.addStretch()

    def show_at_cursor(self):
        """在鼠标附近显示面板"""
        from PySide6.QtGui import QCursor
        cursor_pos = QCursor.pos()
        # 确保面板不超出屏幕
        screen = QApplication.primaryScreen().availableGeometry()
        x = min(cursor_pos.x() - self.width() // 2, screen.right() - self.width())
        x = max(x, screen.left())
        y = min(cursor_pos.y() + 20, screen.bottom() - self.height())
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_box.setFocus()

    def toggle_visible(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.refresh()
            self.show_at_cursor()

    # ── 事件 ──────────────────────────────────────────

    def focusOutEvent(self, event):
        """失去焦点时自动隐藏"""
        self.hide()
        self.closed.emit()
        super().focusOutEvent(event)

    # ── 槽函数 ────────────────────────────────────────

    def _on_search(self):
        self.refresh()

    def _on_retention_change(self, text: str):
        days = int(text.replace("天", ""))
        self.db.set_retention_days(days)
        self.db.cleanup()
        self.refresh()

    def _on_card_clicked(self, record_id: int):
        """点击卡片 → 复制到剪贴板"""
        record = self.db.get_by_id(record_id)
        if not record:
            return
        clipboard = QApplication.clipboard()
        if record["content_type"] == "text":
            clipboard.setText(record["text_content"])
        else:
            image_path = record.get("image_path", "")
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    clipboard.setPixmap(pixmap)
        self.hide()
        self.closed.emit()

    def _on_pin_toggle(self, record_id: int):
        self.db.toggle_pin(record_id)
        self.refresh()

    def _on_delete(self, record_id: int):
        self.db.delete(record_id)
        self.refresh()

    def _on_clear_all(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有非置顶记录吗？\n置顶的记录会被保留。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_all()
            self.refresh()
