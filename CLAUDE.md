# 剪贴板历史工具 — 项目指引

## 项目概述

Windows 历史剪贴板管理工具。以系统托盘小工具形态运行，自动记录文字和图片复制内容，支持搜索、置顶、删除，以及按存储天数自动清理。

**用户：** 编程小白，需要稳定、简单、开箱即用的工具。

## 关键文件速查

| 用途 | 路径 |
|------|------|
| 📋 用户需求规格 | [docs/requirements.md](docs/requirements.md) |
| 🔧 技术规范 | [docs/technical-spec.md](docs/technical-spec.md) |
| 🎨 UI 设计规范 | [docs/ui-design-spec.md](docs/ui-design-spec.md) |
| 📅 分阶段开发计划 | [docs/development-plan.md](docs/development-plan.md) |
| 📝 开发日志目录 | [dev-logs/](dev-logs/) |
| 💾 数据库模块 | [src/database.py](src/database.py) |
| 👂 剪贴板监听 | [src/clipboard_monitor.py](src/clipboard_monitor.py) |
| 🪟 主面板 UI | [src/main_window.py](src/main_window.py) |
| 🔔 系统托盘 | [src/tray_icon.py](src/tray_icon.py) |
| ⌨️ 全局热键 | [src/hotkey.py](src/hotkey.py) |
| 🎨 主题样式 | [src/styles.py](src/styles.py) |
| 🚀 程序入口 | [app.py](app.py) |
| 📦 依赖清单 | [requirements.txt](requirements.txt) |
| ⚡ 一键安装 | [setup.bat](setup.bat) |

## 工作约定

### 1. 分阶段推进

严格按照 [docs/development-plan.md](docs/development-plan.md) 中定义的 6 个阶段（0→5）逐步开发。**每个阶段独立可验证，完成并确认后再进入下一阶段**，不要跳跃或一口气做太多。

### 2. 开发日志

- **每次会话开始时**，在 `dev-logs/` 下创建以当天日期命名的日志文件（如 `2026-05-30.md`）
- 日志文件应包含：
  - **今日目标**：本次会话要完成什么
  - **已完成**：每完成一项打勾记录
  - **待办事项**：发现的后续需要处理的事项
  - **遇到的问题**：任何阻塞或技术难点
  - **验证结果**：测试结果记录
- **会话结束时**，更新日志文件

### 3. 修改前先阅读

在修改任何源代码文件之前，先阅读：
1. 该文件当前的内容
2. `docs/` 中相关的规范文档
3. 确保修改符合已定义的设计规范

### 4. 每步可验证

每个模块完成后，使用 `python` 命令直接测试验证，不要等到全部写完再测试。开发计划中每个阶段都列出了具体的测试方法。

### 5. 保持简洁

- 代码注释用中文
- 变量和函数命名用英文（遵循 Python 惯例）
- 不引入不必要的依赖
- 不实现需求文档中未提及的功能

### 6. 面向用户

最终交付的是一个普通用户双击就能用的软件。始终保持这个意识：
- `setup.bat` 要简单可靠
- 错误提示要友好（中文）
- 不需要用户打开命令行就能运行（最终打包为 exe）

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 主语言 |
| PySide6 | 6.5.0+ | GUI 框架（Qt for Python） |
| SQLite | 内置 | 本地数据库 |
| pywin32 | 306+ | Windows 原生剪贴板 API + 热键 |
| Pillow | 10.0.0+ | 图片处理 |

## 项目结构

```
clipboard-history/
├── CLAUDE.md              ← 你在这里
├── app.py                 # 程序入口
├── requirements.txt       # 依赖清单
├── setup.bat              # 一键安装（双击运行）
├── docs/                  # 规范文档（开发时参考）
│   ├── requirements.md
│   ├── technical-spec.md
│   ├── ui-design-spec.md
│   └── development-plan.md
├── dev-logs/              # 每日开发日志
│   └── YYYY-MM-DD.md
├── src/                   # 源代码
│   ├── __init__.py
│   ├── database.py
│   ├── clipboard_monitor.py
│   ├── main_window.py
│   ├── tray_icon.py
│   ├── hotkey.py
│   └── styles.py
└── data/                  # 运行时数据（自动创建，不提交 git）
    ├── clipboard.db
    └── images/
```
