# 技术规范

## 技术栈

| 层面 | 选择 | 版本要求 |
|------|------|----------|
| 语言 | Python 3 | 3.11 及以上 |
| UI 框架 | PySide6 | 6.5.0 及以上 |
| 数据库 | SQLite | Python 内置 |
| 剪贴板 API | pywin32 | 306 及以上 |
| 图片处理 | Pillow | 10.0.0 及以上 |

## 项目结构

```
clipboard-history/
├── CLAUDE.md
├── app.py                     # 程序入口
├── requirements.txt
├── setup.bat
├── docs/
│   ├── requirements.md
│   ├── technical-spec.md      # 本文件
│   ├── ui-design-spec.md
│   └── development-plan.md
├── dev-logs/
│   └── YYYY-MM-DD.md
├── src/
│   ├── __init__.py
│   ├── database.py
│   ├── clipboard_monitor.py
│   ├── main_window.py
│   ├── tray_icon.py
│   ├── hotkey.py
│   └── styles.py
└── data/
    ├── clipboard.db
    └── images/
```

## 模块职责

### database.py — 数据持久层
- 管理 SQLite 连接和表创建
- 提供剪贴板记录的增删改查接口
- 实现过期记录自动清理
- 管理用户设置（存储天数）

### clipboard_monitor.py — 剪贴板监听
- 在后台线程中每 300ms 轮询系统剪贴板
- 计算内容哈希，避免重复记录
- 区分文字和图片类型
- 图片保存为 PNG 到 `data/images/`

### main_window.py — 主面板 UI
- 弹出式窗口，置顶显示
- 搜索栏 + 存储天数选择 + 卡片列表 + 底部操作栏
- 卡片渲染：文字截断预览 / 图片缩略图
- 交互：点击复制、悬停显示操作按钮
- 响应热键信号显示/隐藏

### tray_icon.py — 系统托盘
- 创建托盘图标
- 左键点击切换面板显示
- 右键菜单
- 开机自启动设置

### hotkey.py — 全局热键
- 注册 Ctrl+Shift+V
- 通过 Windows API 实现系统级热键
- 热键触发时通知主窗口切换显示

### styles.py — 样式主题
- 定义全局 QSS 样式表
- 统一颜色、字体、间距、圆角等视觉规范

## 数据库设计

### 表：clipboard_history

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| content_type | TEXT | NOT NULL | "text" 或 "image" |
| text_content | TEXT | NULLABLE | 文字内容 |
| image_path | TEXT | NULLABLE | 图片文件路径 |
| created_at | TEXT | NOT NULL | ISO 格式时间戳 |
| pinned | INTEGER | NOT NULL DEFAULT 0 | 0=普通, 1=置顶 |

### 表：settings

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| key | TEXT | PRIMARY KEY | 设置项名称 |
| value | TEXT | NOT NULL | 设置值 |

默认设置项：
- `retention_days` = `"3"`

## 数据流

```
剪贴板变化 → clipboard_monitor(后台线程)
                ├─ 计算哈希（去重）
                ├─ 判断类型
                ├─ database.add_text() 或 database.add_image()
                └─ 图片另存为 data/images/{id}.png

用户打开面板 → database.get_all(search, limit)
                └─ 返回排序后的卡片数据
                   (pinned DESC, created_at DESC)

用户操作卡片 → 点击 → 写回剪贴板 + 隐藏面板
               → 置顶 → database.toggle_pin()
               → 删除 → database.delete()

自动清理 → 每次启动 / 每次添加记录后
           → database.cleanup(retention_days)
           → DELETE WHERE pinned=0 AND created_at < 截止时间
```

## 剪贴板轮询机制

- 轮询间隔：300ms
- 去重方式：对内容计算 MD5 哈希，与上一次哈希对比
- 文字获取：`QApplication.clipboard().text()`
- 图片获取：`QApplication.clipboard().image()` → QImage → Pillow Image → 保存 PNG
- 空内容跳过（用户可能按了 Ctrl+C 但没选中内容）

## 性能考量

- 轮询线程使用 `QThread`，不阻塞 GUI 主线程
- 卡片列表最多显示 200 条，超过时分页或滚动加载
- 图片缩略图在渲染时实时生成，不额外存储
- 数据库使用 WAL 模式提升并发性能
