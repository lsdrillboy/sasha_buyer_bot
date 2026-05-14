from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CURATOR_USERNAME

router = Router()


@router.message(F.text == "📞 Связаться с куратором")
async def contact_curator(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not CURATOR_USERNAME:
        await message.answer(
            "ℹ️ Контакт куратора не настроен.\n"
            "Обратитесь к администратору бота."
        )
        return

    username = CURATOR_USERNAME.lstrip("@")
    b = InlineKeyboardBuilder()
    b.button(text="💬 Написать куратору", url=f"https://t.me/{username}")

    await message.answer(
        "📞 <b>Связь с куратором</b>\n\n"
        "Если есть вопросы по работе с площадками — куратор поможет разобраться.",
        parse_mode="HTML",
        reply_markup=b.as_markup(),
    )
