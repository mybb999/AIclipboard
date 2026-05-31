# 分阶段开发计划

## 总览

| 阶段 | 名称 | 预计文件 | 核心目标 |
|------|------|----------|----------|
| 0 | 项目初始化 | 文档 + 配置 | 搭好骨架 |
| 1 | 数据层 | database.py | 数据可读写 |
| 2 | 剪贴板监听 | clipboard_monitor.py | 自动记录 |
| 3 | 主面板 UI | main_window.py + styles.py | 可见可操作 |
| 4 | 系统托盘 + 热键 | tray_icon.py + hotkey.py | 完整运行 |
| 5 | 组装 + 集成测试 | app.py | 全流程打通 |

## 阶段 0：项目初始化

**目标：** 创建完整项目骨架，确保文档齐全、依赖可安装

**产出清单：**
- [ ] 目录结构（src/, docs/, dev-logs/, data/）
- [ ] requirements.txt（PySide6 + pywin32 + Pillow）
- [ ] setup.bat（一键安装脚本，含国内镜像加速）
- [ ] docs/requirements.md（需求规格）
- [ ] docs/technical-spec.md（技术规范）
- [ ] docs/ui-design-spec.md（UI 设计规范）
- [ ] docs/development-plan.md（本文件）
- [ ] CLAUDE.md（项目指引）
- [ ] dev-logs/2026-05-30.md（首日日志）
- [ ] src/__init__.py

**完成标准：**
- `setup.bat` 可成功运行并安装所有依赖
- 所有文档符合模板、内容完整

---

## 阶段 1：数据层

**目标：** 实现 SQLite 数据库的完整读写能力

**产出清单：**
- [ ] `src/database.py` 完整模块
  - `__init__()` — 创建连接、初始化表
  - `add_text(text)` — 添加文字记录
  - `add_image(image_path)` — 添加图片记录
  - `get_all(search, limit)` — 查询列表
  - `toggle_pin(id)` — 切换置顶
  - `delete(id)` — 删除
  - `delete_all()` — 清空全部（保留置顶）
  - `get_retention_days()` — 读取保留天数
  - `set_retention_days(days)` — 设置保留天数
  - `cleanup()` — 按天数清理过期非置顶记录

**测试方法：**
```python
# 在项目根目录运行
python -c "
from src.database import Database
db = Database('data/test.db')
db.add_text('第一条测试记录')
db.add_text('第二条测试记录')
print(db.get_all())
db.toggle_pin(1)
print(db.get_all())
db.cleanup()
db.delete_all()
"
```

**完成标准：**
- 数据库文件自动创建
- 所有增删改查操作正确返回
- 清理逻辑正确（不删除置顶项）

---

## 阶段 2：剪贴板监听

**目标：** 实现后台剪贴板变化监听，自动存入数据库

**产出清单：**
- [ ] `src/clipboard_monitor.py`
  - `ClipboardMonitor(QThread)` 类
  - `start()` / `stop()` 控制监听
  - 300ms 轮询间隔
  - MD5 哈希去重
  - 文字检测 → `db.add_text()`
  - 图片检测 → 保存 PNG → `db.add_image()`
  - `new_record` 信号（通知 UI 刷新）

**测试方法：**
```python
python -c "
import sys, time
from PySide6.QtWidgets import QApplication
from src.database import Database
from src.clipboard_monitor import ClipboardMonitor

app = QApplication(sys.argv)
db = Database()
monitor = ClipboardMonitor(db)
monitor.new_record.connect(lambda: print('新记录:', db.get_all()[0]))
monitor.start()
print('监听已启动，去复制一些文字或图片吧... (10秒后自动停止)')
time.sleep(10)
monitor.stop()
"
```

**完成标准：**
- 复制文字后数据库中自动出现记录
- 复制图片后数据库中出现记录 + data/images/ 下有图片文件
- 重复复制相同内容不产生重复记录

---

## 阶段 3：主面板 UI

**目标：** 实现完整的可视化历史面板

**产出清单：**
- [ ] `src/styles.py`
  - `get_stylesheet()` 函数 → 返回 QSS 字符串
  - 包含所有颜色、字体、间距定义
- [ ] `src/main_window.py`
  - `MainWindow(QWidget)` 类
  - 搜索框（`QLineEdit` + 🔍 图标）
  - 存储天数下拉框（`QComboBox`：1天/3天/5天）
  - 卡片列表（`QScrollArea` + 动态卡片 widget）
  - 底部操作栏（清空按钮 + 记录计数）
  - 文字卡片组件 `TextCard`
  - 图片卡片组件 `ImageCard`
  - 单击复制 + 隐藏
  - 悬停显示操作按钮

**测试方法：**
```python
python -c "
import sys
from PySide6.QtWidgets import QApplication
from src.database import Database
from src.main_window import MainWindow

app = QApplication(sys.argv)
db = Database()
# 先插入一些测试数据
for i in range(20):
    db.add_text(f'测试记录 {i+1}: 这是一段模拟的复制文字内容...')
window = MainWindow(db)
window.show()
app.exec()
"
```

**完成标准：**
- 窗口正确显示，淡蓝色主题
- 卡片按时间降序排列
- 搜索框实时过滤
- 点击卡片复制到剪贴板
- 置顶/删除功能正常
- 存储天数切换生效

---

## 阶段 4：系统托盘 + 热键

**目标：** 实现完整的系统托盘运行能力和全局热键

**产出清单：**
- [ ] `src/tray_icon.py`
  - `TrayIcon(QSystemTrayIcon)` 类
  - 程序化生成图标（QPainter 绘制剪贴板图标）
  - 左键点击 → 切换面板显示
  - 右键菜单 → 显示历史 / 开机自启 / 退出
  - 开机自启：创建/删除 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\` 下的快捷方式
- [ ] `src/hotkey.py`
  - `GlobalHotkey(QObject)` 类
  - 注册 Ctrl+Shift+V（MOD_CONTROL + MOD_SHIFT + VK_V）
  - `activated` 信号

**测试方法：**
- 启动后检查托盘图标出现
- 左键点击打开面板
- 右键菜单各选项正常
- Ctrl+Shift+V 全局触发面板切换
- 开机自启勾选后检查启动文件夹

**完成标准：**
- 托盘图标正常显示和响应
- 全局热键在任何窗口下都能触发
- 开机自启文件正确创建和删除
- 退出时资源完全释放

---

## 阶段 5：组装 + 集成测试

**目标：** 串联所有模块，完整运行

**产出清单：**
- [ ] `app.py`
  - 创建 `QApplication`
  - 初始化 `Database`
  - 启动 `ClipboardMonitor`
  - 创建 `MainWindow`
  - 创建 `TrayIcon`
  - 注册 `GlobalHotkey`
  - 连接所有信号/槽
  - 执行初始清理 `db.cleanup()`

**集成测试清单：**
- [ ] 启动程序 → 托盘图标出现
- [ ] 复制文字 → 点开面板 → 文字卡片存在
- [ ] 复制图片 → 点开面板 → 图片卡片存在（缩略图正确）
- [ ] 搜索 → 列表过滤正确
- [ ] 点击卡片 → 内容回到剪贴板 → 可粘贴验证
- [ ] 置顶 → 卡片移到最上面
- [ ] 删除 → 卡片消失
- [ ] 清空全部 → 确认对话框 → 非置顶记录清除
- [ ] 存储天数改为1天 → 修改系统时间 → 过期记录被清理（置顶的保留）
- [ ] Ctrl+Shift+V → 面板弹出/隐藏
- [ ] 点击面板外部 → 面板隐藏
- [ ] 退出程序 → 托盘图标消失 → 进程结束
