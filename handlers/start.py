from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID
from database import upsert_user
from keyboards.kb import main_menu_kb

router = Router()

_WELCOME = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Это твой личный помощник по работе с корейскими площадками.\n"
    "Выбери нужный раздел:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(_WELCOME, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    await message.answer(f"Ваш chat_id: <code>{message.from_user.id}</code>", parse_mode="HTML")


@router.message(F.from_user.id == ADMIN_ID, F.video | F.document)
async def capture_file_id(message: Message) -> None:
    """Admin only: send any video/document to get its file_id for lessons.json."""
    if message.video:
        fid = message.video.file_id
        kind = "video"
    else:
        fid = message.document.file_id
        kind = "document"
    await message.reply(
        f"<b>file_id ({kind}):</b>\n<code>{fid}</code>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(_WELCOME, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()
