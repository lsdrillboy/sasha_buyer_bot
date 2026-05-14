from __future__ import annotations

import json
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

_PATH = Path(__file__).parent.parent / "data" / "suppliers.json"
_cache: dict = {}


def _load() -> dict:
    global _cache
    if not _cache:
        with open(_PATH, encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def _logistics_list_kb():
    b = InlineKeyboardBuilder()
    for c in _load()["logistics"]:
        b.button(
            text=f"{c['emoji']} {c['name']} — {c['type_label']}",
            callback_data=f"log:{c['id']}",
        )
    b.adjust(1)
    return b.as_markup()


def _contact_kb(contact: dict):
    b = InlineKeyboardBuilder()
    if contact.get("whatsapp"):
        b.button(
            text="💬 Написать в WhatsApp",
            url=f"https://wa.me/{contact['whatsapp']}",
        )
    if contact.get("telegram"):
        b.button(
            text="💬 Открыть в Telegram",
            url=f"https://t.me/{contact['telegram']}",
        )
    b.button(text="⬅️ К списку логистики", callback_data="log:list")
    b.adjust(1)
    return b.as_markup()


def _render_contact(c: dict) -> str:
    lines = [f"{c['emoji']} <b>{c['name']} — {c['type_label']}</b>", ""]

    if c.get("directions"):
        lines.append(f"📍 Направления: {', '.join(c['directions'])}")

    if c.get("phone"):
        lines.append(f"📞 Телефон: <code>{c['phone']}</code>")

    if c.get("address"):
        lines.append(f"\n📍 Адрес ЛК:\n<code>{c['address']}</code>")

    if c.get("warehouse_1"):
        lines.append(f"\n📍 Адрес склада:\n<code>{c['warehouse_1']}</code>")

    if c.get("price"):
        lines.append(f"\n💰 Тариф: {c['price']}")

    if c.get("delivery"):
        lines.append(f"⏱ Сроки: {c['delivery']}")

    if c.get("note_positive"):
        lines.append(f"✅ {c['note_positive']}")

    if c.get("telegram"):
        lines.append(f"\n💬 Telegram: @{c['telegram']}")

    if c.get("note"):
        lines.append(f"\nℹ️ {c['note']}")

    if c.get("note_warning"):
        lines.append(f"\n⚠️ {c['note_warning']}")

    return "\n".join(lines)


_LIST_TEXT = "🚚 <b>Логистика и отправка</b>\n\nВыберите способ:"


@router.message(F.text == "🚚 Логистика и отправка")
async def show_logistics(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        _LIST_TEXT, parse_mode="HTML", reply_markup=_logistics_list_kb()
    )


@router.callback_query(F.data == "log:list")
async def cb_log_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.edit_text(
            _LIST_TEXT, parse_mode="HTML", reply_markup=_logistics_list_kb()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            _LIST_TEXT, parse_mode="HTML", reply_markup=_logistics_list_kb()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("log:"))
async def cb_contact(callback: CallbackQuery) -> None:
    cid = callback.data[len("log:"):]
    contact = next((c for c in _load()["logistics"] if c["id"] == cid), None)
    if not contact:
        await callback.answer("Не найдено", show_alert=True)
        return

    text = _render_contact(contact)
    kb = _contact_kb(contact)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
