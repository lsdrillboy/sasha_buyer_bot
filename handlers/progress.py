from __future__ import annotations

import json
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import get_completed_lessons

router = Router()


def _load_lessons() -> list[dict]:
    path = Path(__file__).parent.parent / "data" / "lessons.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["lessons"]


@router.message(F.text == "⚙️ Мой прогресс")
async def show_progress(message: Message, state: FSMContext) -> None:
    await state.clear()
    lessons = _load_lessons()
    completed = await get_completed_lessons(message.from_user.id)

    total = len(lessons)
    done = len(completed)
    pct = int(done / total * 100) if total else 0

    filled = int(pct / 10)
    bar = "▓" * filled + "░" * (10 - filled)

    lines = [
        "⚙️ <b>Мой прогресс</b>\n",
        f"Пройдено уроков: <b>{done} / {total}</b>",
        f"[{bar}] {pct}%\n",
    ]
    for lesson in lessons:
        mark = "✅" if lesson["id"] in completed else "🔲"
        lines.append(f"{mark} Урок {lesson['id']}: {lesson['title']}")

    await message.answer("\n".join(lines), parse_mode="HTML")
