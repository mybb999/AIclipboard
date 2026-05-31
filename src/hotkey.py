"""
全局热键模块
============
使用 GetAsyncKeyState 轮询检测 Ctrl+Shift+V 组合键。
不依赖窗口句柄和原生消息过滤器，稳定可靠。
"""

import win32api
import win32con
from PySide6.QtCore import QObject, Signal, QTimer


class GlobalHotkey(QObject):
    """全局热键管理器（轮询方式）"""

    activated = Signal()  # Ctrl+Shift+V 被按下时发射

    _VK_V = 0x56

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._was_pressed = False  # 防止重复触发（按下不放只触发一次）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_keys)

    def register(self):
        """开始监听热键"""
        if self._enabled:
            return
        self._enabled = True
        self._was_pressed = False
        self._timer.start(80)  # 每 80ms 检查一次按键状态
        print("[热键] 已启用 Ctrl+Shift+V")

    def unregister(self):
        """停止监听热键"""
        self._enabled = False
        self._timer.stop()
        print("[热键] 已停用")

    @property
    def registered(self) -> bool:
        return self._enabled

    def _check_keys(self):
        """检查 Ctrl+Shift+V 是否同时按下"""
        try:
            ctrl = win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000
            shift = win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000
            v_key = win32api.GetAsyncKeyState(self._VK_V) & 0x8000
        except Exception:
            return

        is_pressed = bool(ctrl and shift and v_key)

        if is_pressed and not self._was_pressed:
            # 刚按下（上升沿触发）
            self.activated.emit()
            self._was_pressed = True
        elif not is_pressed:
            # 已松开，重置状态
            self._was_pressed = False
