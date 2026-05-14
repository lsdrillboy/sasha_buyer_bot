from __future__ import annotations

import aiosqlite
from datetime import datetime

DB_PATH = "buyer_bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id    INTEGER PRIMARY KEY,
                username       TEXT,
                registered_at  TEXT NOT NULL,
                last_active_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lesson_progress (
                telegram_id  INTEGER NOT NULL,
                lesson_id    INTEGER NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (telegram_id, lesson_id)
            );
        """)
        await db.commit()


async def upsert_user(telegram_id: int, username: str | None) -> None:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, registered_at, last_active_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                last_active_at = excluded.last_active_at
            """,
            (telegram_id, username or "", now, now),
        )
        await db.commit()


async def mark_lesson_complete(telegram_id: int, lesson_id: int) -> None:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO lesson_progress (telegram_id, lesson_id, completed_at)
            VALUES (?, ?, ?)
            """,
            (telegram_id, lesson_id, now),
        )
        await db.commit()


async def get_completed_lessons(telegram_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT lesson_id FROM lesson_progress WHERE telegram_id = ?",
            (telegram_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
