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
            CREATE TABLE IF NOT EXISTS payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                file_id      TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
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


# ── Payments ──────────────────────────────────────────────────────────────────

async def create_payment(telegram_id: int, file_id: str) -> int:
    """Save new pending payment, return its auto-generated ID."""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO payments (telegram_id, file_id, status, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?)
            """,
            (telegram_id, file_id, now, now),
        )
        await db.commit()
        return cursor.lastrowid


async def update_payment_status(payment_id: int, status: str) -> None:
    """Update payment status: 'approved' | 'rejected'."""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, payment_id),
        )
        await db.commit()


async def get_user_payment_status(telegram_id: int) -> str | None:
    """Return latest payment status for a user, or None if no payments."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT status FROM payments
            WHERE telegram_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def is_payment_approved(telegram_id: int) -> bool:
    """Return True if user has at least one approved payment."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM payments WHERE telegram_id = ? AND status = 'approved' LIMIT 1",
            (telegram_id,),
        ) as cursor:
            return await cursor.fetchone() is not None
