from __future__ import annotations

import json
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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


class SupplierSearch(StatesGroup):
    waiting = State()


def _markets_kb():
    b = InlineKeyboardBuilder()
    for m in _load()["markets"]:
        count = len(m["wechat_ids"])
        b.button(
            text=f"{m['emoji']} {m['name']} — {m['description']} ({count})",
            callback_data=f"sup:tc:{m['key']}",
        )
    b.button(text="🔍 Поиск по WeChat ID", callback_data="sup:search")
    b.adjust(1)
    return b.as_markup()


def _back_markets_kb():
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К списку ТЦ", callback_data="sup:list")
    return b.as_markup()


_LIST_TEXT = (
    "🏪 <b>Поставщики (WeChat ID)</b>\n\n"
    "ℹ️ Нажмите на ID — он скопируется в буфер обмена\n\n"
    "Выберите торговый центр:"
)


@router.message(F.text == "🏪 Поставщики")
async def show_suppliers(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_LIST_TEXT, parse_mode="HTML", reply_markup=_markets_kb())


@router.callback_query(F.data == "sup:list")
async def cb_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.edit_text(
            _LIST_TEXT, parse_mode="HTML", reply_markup=_markets_kb()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            _LIST_TEXT, parse_mode="HTML", reply_markup=_markets_kb()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sup:tc:"))
async def cb_tc(callback: CallbackQuery) -> None:
    key = callback.data[len("sup:tc:"):]
    market = next((m for m in _load()["markets"] if m["key"] == key), None)
    if not market:
        await callback.answer("Не найдено", show_alert=True)
        return

    contact = market.get("contact")
    wechat_ids = market.get("wechat_ids", [])

    if contact and not wechat_ids:
        # Market with a direct contact (e.g. Cosmic) — show contact card
        lines = [
            f"{market['emoji']} <b>{market['name']} — {market['description']}</b>",
            "",
            f"📞 Телефон: <code>{contact['phone']}</code>",
        ]
        text = "\n".join(lines)
        b = InlineKeyboardBuilder()
        if contact.get("whatsapp"):
            b.button(
                text="💬 Написать в WhatsApp",
                url=f"https://wa.me/{contact['whatsapp']}",
            )
        b.button(text="⬅️ К списку ТЦ", callback_data="sup:list")
        b.adjust(1)
        kb = b.as_markup()
    else:
        lines = [
            f"{market['emoji']} <b>{market['name']} — {market['description']}</b>",
            f"<i>{len(wechat_ids)} поставщиков</i>",
            "",
            "Нажмите на ID для копирования:",
            "",
        ]
        for entry in wechat_ids:
            line = f"• <code>{entry['id']}</code>"
            if entry.get("note"):
                line += f"  <i>({entry['note']})</i>"
            lines.append(line)
        text = "\n".join(lines)
        kb = _back_markets_kb()

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "sup:search")
async def cb_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupplierSearch.waiting)
    await callback.message.answer("🔍 Введите часть WeChat ID для поиска:")
    await callback.answer()


@router.message(SupplierSearch.waiting)
async def process_search(message: Message, state: FSMContext) -> None:
    query = message.text.strip().lower()
    await state.clear()

    results = []
    for m in _load()["markets"]:
        for entry in m["wechat_ids"]:
            if query in entry["id"].lower():
                results.append((m, entry))

    b = InlineKeyboardBuilder()
    b.button(text="🔍 Новый поиск", callback_data="sup:search")
    b.button(text="⬅️ К списку ТЦ", callback_data="sup:list")
    b.adjust(1)

    if not results:
        await message.answer(
            f"🔍 По запросу «{query}» ничего не найдено.",
            reply_markup=b.as_markup(),
        )
        return

    lines = [f"🔍 <b>Результаты по «{query}»:</b>", ""]
    for m, entry in results:
        line = f"{m['emoji']} {m['name']} → <code>{entry['id']}</code>"
        if entry.get("note"):
            line += f"  <i>({entry['note']})</i>"
        lines.append(line)

    await message.answer(
        "\n".join(lines), parse_mode="HTML", reply_markup=b.as_markup()
    )
