"""
剪贴板监听模块
==============
后台线程，每 300ms 轮询系统剪贴板。
检测到新内容时自动存入数据库。
"""

import hashlib
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage


class ClipboardMonitor(QThread):
    """剪贴板变化监听器（后台线程）"""

    # 信号：新记录已添加，携带记录 id 和类型
    new_record = Signal(int, str)

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.db = database
        self._running = False
        self._last_hash = ""       # 上次内容的 MD5 哈希（去重用）
        self._app = None           # QApplication 引用

    def set_app(self, app: QApplication):
        """设置 QApplication 引用（访问剪贴板需要）"""
        self._app = app

    def run(self):
        """线程主循环"""
        self._running = True
        self._last_hash = ""
        while self._running:
            try:
                self._check_clipboard()
            except Exception:
                pass  # 忽略单次错误，继续轮询
            self.msleep(300)  # 300ms 轮询间隔

    def stop(self):
        """停止监听"""
        self._running = False
        self.wait(1000)  # 等待线程结束（最多1秒）

    def _check_clipboard(self):
        """检查剪贴板是否有新内容"""
        if self._app is None:
            return

        clipboard = self._app.clipboard()
        if clipboard is None:
            return

        # 1. 检查图片
        image = clipboard.image()
        if image is not None and not image.isNull():
            self._handle_image(image)
            return

        # 2. 检查文字
        text = clipboard.text()
        if text and text.strip():
            self._handle_text(text.strip())

    def _handle_text(self, text: str):
        """处理文字内容"""
        content_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        if content_hash == self._last_hash:
            return  # 重复内容，跳过

        self._last_hash = content_hash
        record_id = self.db.add_text(text)
        self.new_record.emit(record_id, "text")

    def _handle_image(self, image: QImage):
        """处理图片内容"""
        # 将 QImage 转为字节数据做哈希去重
        byte_array = image.bits()
        if byte_array is None:
            return
        raw_bytes = bytes(byte_array)
        content_hash = hashlib.md5(raw_bytes).hexdigest()
        if content_hash == self._last_hash:
            return  # 重复内容，跳过

        self._last_hash = content_hash

        # 保存图片文件，以记录 id 命名（先占位再更新）
        import os
        image_dir = os.path.join("data", "images")
        os.makedirs(image_dir, exist_ok=True)

        # 先插入数据库获取 id
        temp_path = os.path.join(image_dir, "_temp.png")
        record_id = self.db.add_image(temp_path)

        # 用真正的 id 重命名保存
        real_path = os.path.join(image_dir, f"{record_id}.png")
        image.save(real_path, "PNG")
        self.db.conn.execute(
            "UPDATE clipboard_history SET image_path = ? WHERE id = ?",
            (real_path, record_id)
        )
        self.db.conn.commit()

        self.new_record.emit(record_id, "image")
