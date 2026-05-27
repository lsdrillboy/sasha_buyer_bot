from __future__ import annotations

import json
import re
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID
from database import get_completed_lessons, is_payment_approved, mark_lesson_complete
from keyboards.kb import lesson_kb, lessons_list_kb

router = Router()

_CAPTION_LIMIT = 1020  # Telegram caption limit is 1024, safe margin


def _load() -> list[dict]:
    path = Path(__file__).parent.parent / "data" / "lessons.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["lessons"]


def _by_id(lesson_id: int) -> dict | None:
    return next((l for l in _load() if l["id"] == lesson_id), None)


def _next_num(lesson: dict) -> str | None:
    nid = lesson.get("next_lesson")
    if not nid:
        return None
    nxt = _by_id(nid)
    return nxt.get("number", str(nid)) if nxt else None


def _visible_len(text: str) -> int:
    return len(re.sub(r"<[^>]+>", "", text))


def _render(lesson: dict) -> str:
    num = lesson.get("number", str(lesson["id"]))
    parts = [f"<b>Урок {num}: {lesson['title']}</b>"]
    if lesson.get("subtitle"):
        parts.append(f"<i>{lesson['subtitle']}</i>")
    parts.append("")
    parts.append(lesson["text"])
    if lesson.get("warnings"):
        parts.append("\n⚠️ <b>Важно:</b>")
        for w in lesson["warnings"]:
            parts.append(f"• {w}")
    return "\n".join(parts)


def _render_short(lesson: dict) -> str:
    """Render without warnings — used when full text exceeds caption limit."""
    num = lesson.get("number", str(lesson["id"]))
    parts = [f"<b>Урок {num}: {lesson['title']}</b>"]
    if lesson.get("subtitle"):
        parts.append(f"<i>{lesson['subtitle']}</i>")
    parts.append("")
    parts.append(lesson["text"])
    return "\n".join(parts)


@router.message(F.text == "🎓 Уроки")
async def show_lessons(message: Message, state: FSMContext) -> None:
    await state.clear()
    uid = message.from_user.id

    # Admin always has access; others must have approved payment
    if uid != ADMIN_ID and not await is_payment_approved(uid):
        await message.answer(
            "🔒 <b>Доступ закрыт</b>\n\n"
            "Уроки доступны только после оплаты.\n\n"
            "Нажмите «💳 Оплата», оплатите и загрузите чек — "
            "после подтверждения администратором доступ откроется автоматически.",
            parse_mode="HTML",
        )
        return

    completed = await get_completed_lessons(uid)
    await message.answer(
        "🎓 <b>Уроки по работе с площадками</b>\n\nВыбери урок:",
        parse_mode="HTML",
        reply_markup=lessons_list_kb(_load(), completed),
    )


async def _show_lesson_msg(callback: CallbackQuery, lesson: dict) -> None:
    """Core display logic: video+caption in one bubble, or plain text."""
    completed = await get_completed_lessons(callback.from_user.id)
    kb = lesson_kb(lesson, completed, _next_num(lesson))

    if lesson.get("video_file_id"):
        caption = _render(lesson)
        if _visible_len(caption) > _CAPTION_LIMIT:
            caption = _render_short(lesson)

        # Delete the old message (text or video), send fresh video+caption bubble
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass

        if lesson.get("video_type") == "document":
            await callback.message.answer_document(
                document=lesson["video_file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            await callback.message.answer_video(
                video=lesson["video_file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
    else:
        text = _render(lesson)
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except TelegramBadRequest:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("lesson:"))
async def show_lesson(callback: CallbackQuery) -> None:
    lid = int(callback.data.split(":")[1])
    lesson = _by_id(lid)
    if not lesson:
        await callback.answer("Урок не найден", show_alert=True)
        return
    await _show_lesson_msg(callback, lesson)
    await callback.answer()


@router.callback_query(F.data.startswith("lesson_done:"))
async def toggle_done(callback: CallbackQuery) -> None:
    lid = int(callback.data.split(":")[1])
    await mark_lesson_complete(callback.from_user.id, lid)
    lesson = _by_id(lid)
    completed = await get_completed_lessons(callback.from_user.id)
    await callback.answer("✅ Урок отмечен как выполненный!")
    try:
        await callback.message.edit_reply_markup(
            reply_markup=lesson_kb(lesson, completed, _next_num(lesson))
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "back:lessons")
async def back_to_lessons(callback: CallbackQuery) -> None:
    completed = await get_completed_lessons(callback.from_user.id)
    text = "🎓 <b>Уроки по работе с площадками</b>\n\nВыбери урок:"
    kb = lessons_list_kb(_load(), completed)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        # edit_text fails on video messages — delete and send fresh
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
