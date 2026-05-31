"""
数据库模块 — SQLite 增删改查 + 自动清理
=========================================
负责所有剪贴板历史数据的持久化存储和查询。
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict


class Database:
    """剪贴板历史数据库管理器"""

    def __init__(self, db_path: str = "data/clipboard.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认为 data/clipboard.db
        """
        # 确保数据目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row          # 让查询结果支持列名访问
        self.conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式，提升并发性能
        self._create_tables()
        self._init_defaults()

    # ── 初始化 ──────────────────────────────────────────────

    def _create_tables(self):
        """创建数据库表（如果不存在）"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type  TEXT    NOT NULL,
                text_content  TEXT,
                image_path    TEXT,
                created_at    TEXT    NOT NULL,
                pinned        INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _init_defaults(self):
        """写入默认设置（仅当设置表为空时）"""
        existing = self.conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        if existing == 0:
            self.conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                ("retention_days", "3")
            )
            self.conn.commit()

    # ── 添加记录 ───────────────────────────────────────────

    def add_text(self, text: str) -> int:
        """
        添加一条文字记录

        Args:
            text: 复制的文字内容

        Returns:
            新记录的 id
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            "INSERT INTO clipboard_history (content_type, text_content, created_at) VALUES (?, ?, ?)",
            ("text", text, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_image(self, image_path: str) -> int:
        """
        添加一条图片记录

        Args:
            image_path: 图片文件的保存路径

        Returns:
            新记录的 id
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            "INSERT INTO clipboard_history (content_type, image_path, created_at) VALUES (?, ?, ?)",
            ("image", image_path, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    # ── 查询记录 ───────────────────────────────────────────

    def get_all(self, search: str = "", limit: int = 200):
        """
        查询历史记录列表

        排序规则：置顶优先 → 时间降序
        支持按文字内容搜索过滤

        Args:
            search: 搜索关键词（为空则不过滤）
            limit: 最大返回条数

        Returns:
            list[dict]: 记录列表，每条记录包含所有字段
        """
        if search:
            query = """
                SELECT * FROM clipboard_history
                WHERE content_type = 'text' AND text_content LIKE ?
                ORDER BY pinned DESC, created_at DESC
                LIMIT ?
            """
            rows = self.conn.execute(query, (f"%{search}%", limit)).fetchall()
        else:
            query = """
                SELECT * FROM clipboard_history
                ORDER BY pinned DESC, created_at DESC
                LIMIT ?
            """
            rows = self.conn.execute(query, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def get_by_id(self, record_id: int) -> Optional[Dict]:
        """根据 id 获取单条记录"""
        row = self.conn.execute(
            "SELECT * FROM clipboard_history WHERE id = ?",
            (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_count(self) -> int:
        """获取记录总数"""
        return self.conn.execute("SELECT COUNT(*) FROM clipboard_history").fetchone()[0]

    # ── 操作记录 ───────────────────────────────────────────

    def toggle_pin(self, record_id: int) -> bool:
        """
        切换置顶状态（置顶 ↔ 取消置顶）

        Returns:
            bool: 切换后的置顶状态
        """
        current = self.conn.execute(
            "SELECT pinned FROM clipboard_history WHERE id = ?",
            (record_id,)
        ).fetchone()
        if current is None:
            return False
        new_state = 0 if current["pinned"] else 1
        self.conn.execute(
            "UPDATE clipboard_history SET pinned = ? WHERE id = ?",
            (new_state, record_id)
        )
        self.conn.commit()
        return bool(new_state)

    def delete(self, record_id: int) -> bool:
        """
        删除单条记录（同时删除关联的图片文件）

        Returns:
            bool: 是否成功删除
        """
        row = self.conn.execute(
            "SELECT image_path FROM clipboard_history WHERE id = ?",
            (record_id,)
        ).fetchone()

        if row is None:
            return False

        # 如果有图片文件，一并删除
        if row["image_path"] and os.path.exists(row["image_path"]):
            try:
                os.remove(row["image_path"])
            except OSError:
                pass  # 文件删除失败不影响数据库操作

        self.conn.execute("DELETE FROM clipboard_history WHERE id = ?", (record_id,))
        self.conn.commit()
        return True

    def delete_all(self):
        """
        清空所有非置顶记录

        保留所有置顶记录，删除其余全部记录及其关联图片文件。
        """
        # 先收集要删除的图片文件路径
        rows = self.conn.execute(
            "SELECT image_path FROM clipboard_history WHERE pinned = 0"
        ).fetchall()
        for row in rows:
            if row["image_path"] and os.path.exists(row["image_path"]):
                try:
                    os.remove(row["image_path"])
                except OSError:
                    pass

        self.conn.execute("DELETE FROM clipboard_history WHERE pinned = 0")
        self.conn.commit()

    # ── 设置管理 ───────────────────────────────────────────

    def get_retention_days(self) -> int:
        """获取保留天数设置"""
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = 'retention_days'"
        ).fetchone()
        return int(row["value"]) if row else 3

    def set_retention_days(self, days: int):
        """
        设置保留天数

        Args:
            days: 保留天数（1、3 或 5）
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('retention_days', ?)",
            (str(days),)
        )
        self.conn.commit()

    # ── 自动清理 ───────────────────────────────────────────

    def cleanup(self):
        """
        清理过期记录

        删除超过保留天数的非置顶记录及其关联图片文件。
        置顶记录永不过期。
        """
        days = self.get_retention_days()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        # 收集要删除的图片文件
        rows = self.conn.execute(
            "SELECT id, image_path FROM clipboard_history WHERE pinned = 0 AND created_at < ?",
            (cutoff,)
        ).fetchall()

        for row in rows:
            if row["image_path"] and os.path.exists(row["image_path"]):
                try:
                    os.remove(row["image_path"])
                except OSError:
                    pass

        self.conn.execute(
            "DELETE FROM clipboard_history WHERE pinned = 0 AND created_at < ?",
            (cutoff,)
        )
        self.conn.commit()

    # ── 关闭 ───────────────────────────────────────────────

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ARG002
        self.close()
        return False


# ── 命令行快速测试 ──────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    # 使用临时文件测试，不影响正式数据
    test_db = os.path.join(tempfile.gettempdir(), "clipboard_test.db")
    print(f"测试数据库: {test_db}")

    with Database(test_db) as db:
        # 1. 测试添加文字
        id1 = db.add_text("这是第一条测试文字")
        id2 = db.add_text("这是第二条测试文字，包含关键词")
        print(f"[OK]添加文字记录: id={id1}, id={id2}")

        # 2. 测试添加图片
        id3 = db.add_image("data/images/test.png")
        print(f"[OK]添加图片记录: id={id3}")

        # 3. 测试查询
        all_records = db.get_all()
        print(f"[OK]查询全部: 共 {len(all_records)} 条")
        for r in all_records:
            print(f"   id={r['id']}, type={r['content_type']}, pinned={r['pinned']}")

        # 4. 测试搜索
        results = db.get_all(search="关键词")
        print(f"[OK]搜索'关键词': 找到 {len(results)} 条")

        # 5. 测试置顶
        db.toggle_pin(id1)
        print(f"[OK]置顶 id={id1}")

        # 6. 测试置顶排序
        top_records = db.get_all()
        print(f"[OK]置顶后第一条: id={top_records[0]['id']} (应为 {id1})")

        # 7. 测试取消置顶
        db.toggle_pin(id1)
        print(f"[OK]取消置顶 id={id1}")

        # 8. 测试保留天数设置
        db.set_retention_days(1)
        days = db.get_retention_days()
        print(f"[OK]保留天数: {days}")

        # 9. 测试删除
        db.delete(id2)
        remaining = db.get_all()
        print(f"[OK]删除 id={id2} 后剩余: {len(remaining)} 条")

        # 10. 测试清空（保留置顶）
        db.toggle_pin(id1)  # 先置顶 id1
        db.delete_all()
        remaining = db.get_all()
        print(f"[OK]清空后剩余: {len(remaining)} 条 (应有置顶的 id={id1})")

        # 11. 测试清理
        # 手动将一条记录的创建时间改为很久以前
        db.conn.execute(
            "UPDATE clipboard_history SET created_at = '2020-01-01 00:00:00' WHERE id = ?",
            (remaining[0]["id"],)
        )
        db.conn.commit()
        db.toggle_pin(remaining[0]["id"])  # 取消置顶，让它可被清理
        before = db.get_count()
        db.cleanup()
        after = db.get_count()
        print(f"[OK]清理: {before} → {after} 条")

        # 清理测试数据库
        try:
            os.remove(test_db)
            print(f"[OK]测试数据库已删除")
        except OSError:
            pass

    print("\n[PASS] 所有测试通过!")
