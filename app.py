"""
剪贴板历史工具 — 程序入口
==========================
启动所有模块，串联为一个完整的系统托盘应用。
"""
import os
import sys
import socket

# pythonw.exe 环境下无控制台，重定向 stdout/stderr 避免 print() 报错
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from PySide6.QtWidgets import QApplication

from src.database import Database
from src.clipboard_monitor import ClipboardMonitor
from src.main_window import MainWindow
from src.tray_icon import TrayIcon
from src.hotkey import GlobalHotkey


# ── 单实例检测 ──────────────────────────────────────

def _is_already_running() -> bool:
    """检测是否已有实例在运行（通过绑定固定端口）"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 19876))
        # 不关闭 socket，让它一直占用端口直到程序退出
        return False
    except socket.error:
        return True


# ── 主函数 ──────────────────────────────────────────

def main():
    # 0. 单实例检查
    if _is_already_running():
        print("程序已在运行中，请查看系统托盘图标。")
        sys.exit(0)

    # 1. 确保 data 目录存在
    os.makedirs("data/images", exist_ok=True)

    # 2. 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘常驻

    # 3. 初始化数据库 + 启动清理
    db = Database("data/clipboard.db")
    db.cleanup()

    # 4. 创建主面板
    window = MainWindow(db)

    # 5. 注册全局热键 Ctrl+Shift+V（轮询方式，无需 HWND）
    hotkey = GlobalHotkey()
    hotkey.activated.connect(window.toggle_visible)
    hotkey.register()

    # 6. 创建系统托盘
    tray = TrayIcon(window)
    window.closed.connect(lambda: tray.update_tooltip(db.get_count()))

    # 7. 创建并启动剪贴板监听
    monitor = ClipboardMonitor(db)
    monitor.set_app(app)
    monitor.new_record.connect(
        lambda rid, rtype: tray.update_tooltip(db.get_count())
    )
    monitor.start()

    # 8. 干净退出
    def on_quit():
        hotkey.unregister()
        monitor.stop()
        db.close()

    app.aboutToQuit.connect(on_quit)

    # 9. 启动提示
    tray.update_tooltip(db.get_count())
    tray.showMessage(
        "剪贴板历史",
        "已开始监听剪贴板\n按 Ctrl+Shift+V 打开面板",
        TrayIcon.Information,
        2000
    )

    # 10. 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
