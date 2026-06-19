"""
SQLite 数据库管理
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "history.db")


def init_db():
    """初始化数据库表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                image_filename TEXT NOT NULL,
                summary TEXT NOT NULL,
                pipeline TEXT NOT NULL,
                result TEXT,
                total_score REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_record(
    image_path: str,
    image_filename: str,
    summary: str,
    pipeline: str,
) -> int:
    """创建新的历史记录"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO history (image_path, image_filename, summary, pipeline, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (image_path, image_filename, summary, pipeline),
        )
        conn.commit()
        return cursor.lastrowid


def update_record(
    record_id: int,
    result: Dict[str, Any],
    total_score: float,
    status: str = "completed",
):
    """更新记录结果"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE history
            SET result = ?, total_score = ?, status = ?, completed_at = ?
            WHERE id = ?
            """,
            (json.dumps(result, ensure_ascii=False), total_score, status, datetime.now(), record_id),
        )
        conn.commit()


def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    """获取单条记录"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row:
            return _row_to_dict(row)
        return None


def get_all_records(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """获取所有记录（按时间倒序）"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM history
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


def get_total_count() -> int:
    """获取记录总数"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history")
        return cursor.fetchone()[0]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """将数据库行转换为字典"""
    data = dict(row)
    if data.get("result"):
        data["result"] = json.loads(data["result"])
    return data


# 初始化数据库
init_db()

