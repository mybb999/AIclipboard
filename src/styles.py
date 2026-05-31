"""
样式主题模块
============
定义全局 QSS（Qt Style Sheet）样式表。
淡蓝色主色调，简洁圆润风格。
"""


def get_stylesheet() -> str:
    """返回全局 QSS 样式表字符串"""
    return """
    /* ── 全局 ──────────────────────────────── */
    * {
        font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
        font-size: 13px;
        color: #333333;
    }

    /* ── 主窗口 ────────────────────────────── */
    QWidget#MainWindow {
        background-color: #E8F4F8;
        border: 1px solid #A8D8EA;
        border-radius: 10px;
    }

    /* ── 搜索框 ────────────────────────────── */
    QLineEdit#SearchBox {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        min-height: 20px;
    }
    QLineEdit#SearchBox:focus {
        border-color: #7EC8E3;
    }

    /* ── 下拉框 ────────────────────────────── */
    QComboBox#RetentionBox {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 4px 8px;
        min-height: 20px;
        font-size: 12px;
    }
    QComboBox#RetentionBox:hover {
        border-color: #7EC8E3;
    }
    QComboBox#RetentionBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        selection-background-color: #A8D8EA;
        selection-color: #333333;
    }

    /* ── 卡片 ──────────────────────────────── */
    QFrame#Card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 10px;
    }
    QFrame#Card:hover {
        border-color: #A8D8EA;
        background-color: #FAFDFE;
    }
    QFrame#CardPinned {
        background-color: #E8F4F8;
        border: 1px solid #A8D8EA;
        border-radius: 6px;
        padding: 10px;
    }

    /* ── 卡片文字 ──────────────────────────── */
    QLabel#CardContent {
        color: #333333;
        font-size: 13px;
        line-height: 1.4;
    }
    QLabel#CardTime {
        color: #9E9E9E;
        font-size: 11px;
    }
    QLabel#CardBadge {
        color: #7EC8E3;
        font-size: 11px;
        font-weight: bold;
    }

    /* ── 按钮 ──────────────────────────────── */
    QPushButton#ActionBtn {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #666666;
        min-width: 32px;
    }
    QPushButton#ActionBtn:hover {
        background-color: #E8F4F8;
        border-color: #A8D8EA;
        color: #5BA4C9;
    }

    QPushButton#ClearBtn {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 12px;
        color: #666666;
    }
    QPushButton#ClearBtn:hover {
        background-color: #FFE0E0;
        border-color: #FF6B6B;
        color: #FF6B6B;
    }

    QPushButton#DeleteBtn {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        color: #999999;
    }
    QPushButton#DeleteBtn:hover {
        background-color: #FFE0E0;
        color: #FF6B6B;
    }

    QPushButton#PinBtn {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        color: #999999;
    }
    QPushButton#PinBtn:hover {
        background-color: #E8F4F8;
        color: #7EC8E3;
    }

    /* ── 滚动区域 ──────────────────────────── */
    QScrollArea {
        background-color: transparent;
        border: none;
    }
    QScrollBar:vertical {
        background-color: #F5F5F5;
        width: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical {
        background-color: #C0C0C0;
        border-radius: 3px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #A8D8EA;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* ── 提示标签 ──────────────────────────── */
    QLabel#EmptyHint {
        color: #9E9E9E;
        font-size: 14px;
        padding: 40px;
    }
    QLabel#CountLabel {
        color: #9E9E9E;
        font-size: 11px;
    }
    """
