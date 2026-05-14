from __future__ import annotations

import json
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.kb import back_faq_kb, faq_list_kb

router = Router()


def _load() -> list[dict]:
    path = Path(__file__).parent.parent / "data" / "faq.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["items"]


def _by_id(item_id: int) -> dict | None:
    return next((i for i in _load() if i["id"] == item_id), None)


@router.message(F.text == "❓ FAQ / Памятки")
async def show_faq(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "❓ <b>FAQ / Памятки</b>\n\nВыбери тему:",
        parse_mode="HTML",
        reply_markup=faq_list_kb(_load()),
    )


@router.callback_query(F.data.startswith("faq:"))
async def show_item(callback: CallbackQuery) -> None:
    item_id = int(callback.data.split(":")[1])
    item = _by_id(item_id)
    if not item:
        await callback.answer("Не найдено", show_alert=True)
        return

    text = f"{item['icon']} <b>{item['title']}</b>\n\n{item['text']}"
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_faq_kb())
    except TelegramBadRequest:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=back_faq_kb())
    await callback.answer()


@router.callback_query(F.data == "back:faq")
async def back_to_faq(callback: CallbackQuery) -> None:
    text = "❓ <b>FAQ / Памятки</b>\n\nВыбери тему:"
    kb = faq_list_kb(_load())
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
