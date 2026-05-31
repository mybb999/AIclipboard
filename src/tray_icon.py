"""
系统托盘模块
============
任务栏托盘图标、右键菜单、开机自启动管理。
"""

import os
import sys

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPainter, QPixmap, QColor, QBrush, QPen, QFont
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt


def _create_icon() -> QIcon:
    """程序化生成淡蓝色剪贴板托盘图标（16x16）"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 主体矩形（剪贴板）
    painter.setPen(QPen(QColor("#7EC8E3"), 1))
    painter.setBrush(QBrush(QColor("#A8D8EA")))
    painter.drawRoundedRect(2, 1, 10, 12, 2, 2)

    # 顶部夹子
    painter.setPen(QPen(QColor("#5BA4C9"), 1.5))
    painter.setBrush(QBrush(QColor("#7EC8E3")))
    painter.drawRoundedRect(4, 0, 6, 3, 1, 1)

    # 内部线条代表文字
    painter.setPen(QPen(QColor("#FFFFFF"), 0.8))
    painter.drawLine(4, 6, 10, 6)
    painter.drawLine(4, 8, 9, 8)
    painter.drawLine(4, 10, 8, 10)

    painter.end()
    return QIcon(pixmap)


def _get_startup_dir() -> str:
    """获取 Windows 启动文件夹路径"""
    appdata = os.getenv("APPDATA", "")
    return os.path.join(
        appdata,
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )


def _get_startup_shortcut_path() -> str:
    """获取开机自启快捷方式的完整路径"""
    return os.path.join(_get_startup_dir(), "ClipboardHistory.lnk")


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标管理器"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.database = main_window.db

        self.setIcon(_create_icon())
        self.setToolTip("剪贴板历史")
        self.setVisible(True)

        # 右击菜单（保存引用防止被垃圾回收）
        self._menu = QMenu()

        self._show_action = QAction("显示历史", self._menu)
        self._show_action.triggered.connect(self._on_show)
        self._menu.addAction(self._show_action)

        self._menu.addSeparator()

        self._startup_action = QAction("开机自启动", self._menu)
        self._startup_action.setCheckable(True)
        self._startup_action.setChecked(self._is_startup_enabled())
        self._startup_action.triggered.connect(self._on_toggle_startup)
        self._menu.addAction(self._startup_action)

        self._menu.addSeparator()

        self._quit_action = QAction("退出", self._menu)
        self._quit_action.triggered.connect(self._on_quit)
        self._menu.addAction(self._quit_action)

        self.setContextMenu(self._menu)

        # 左键点击
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.Trigger:  # 左键单击
            self.main_window.toggle_visible()

    def _on_show(self):
        self.main_window.refresh()
        self.main_window.show_at_cursor()

    def _on_toggle_startup(self, enabled: bool):
        """切换开机自启动"""
        shortcut_path = _get_startup_shortcut_path()
        if enabled:
            self._create_startup_shortcut(shortcut_path)
        else:
            self._remove_startup_shortcut(shortcut_path)

    def _on_quit(self):
        """退出程序"""
        self.main_window.hide()
        QApplication.quit()

    def update_tooltip(self, count: int):
        """更新托盘悬浮提示"""
        self.setToolTip(f"剪贴板历史 - 共 {count} 条记录")

    # ── 开机自启实现 ─────────────────────────────────

    def _is_startup_enabled(self) -> bool:
        return os.path.exists(_get_startup_shortcut_path())

    def _create_startup_shortcut(self, shortcut_path: str):
        """在启动文件夹创建 .lnk 快捷方式"""
        try:
            # 使用 Windows Script Host 创建快捷方式
            import pythoncom
            from win32com.client import Dispatch

            pythoncom.CoInitialize()
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)

            # 目标：当前运行的 Python + 脚本路径
            python_exe = sys.executable
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            app_path = os.path.join(script_dir, "app.py")
            # 用 pythonw.exe 避免启动时弹出命令行窗口
            pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")

            shortcut.TargetPath = pythonw
            shortcut.Arguments = f'"{app_path}"'
            shortcut.WorkingDirectory = script_dir
            shortcut.Description = "剪贴板历史工具"
            shortcut.Save()
            pythoncom.CoUninitialize()

        except Exception as e:
            print(f"[开机自启] 创建快捷方式失败: {e}")

    def _remove_startup_shortcut(self, shortcut_path: str):
        """删除启动文件夹中的快捷方式"""
        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
        except Exception as e:
            print(f"[开机自启] 删除快捷方式失败: {e}")
