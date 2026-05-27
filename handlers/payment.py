"""Payment flow: show bank details → accept PDF receipt → notify admin → confirm/reject."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID, PAYMENT_AMOUNT, PAYMENT_BANK, PAYMENT_CARD, PAYMENT_RECIPIENT
from database import create_payment, get_user_payment_status, update_payment_status
from keyboards.kb import admin_payment_kb, cancel_payment_kb, main_menu_kb

router = Router()


# ── FSM ───────────────────────────────────────────────────────────────────────

class PaymentState(StatesGroup):
    waiting_receipt = State()


# ── Texts ─────────────────────────────────────────────────────────────────────

_PAYMENT_INFO = (
    "💳 <b>Оплата по реквизитам</b>\n\n"
    "Для получения доступа к материалам переведите оплату по реквизитам ниже:\n\n"
    "🏦 <b>Банк:</b> {bank}\n"
    "💳 <b>Номер карты:</b> <code>{card}</code>\n"
    "👤 <b>Получатель:</b> {recipient}\n"
    "💰 <b>Сумма:</b> <b>{amount}</b>\n\n"
    "После перевода нажмите «Отправить чек» и загрузите квитанцию в формате <b>PDF</b>."
)

_WAIT_RECEIPT = (
    "📎 <b>Загрузите чек об оплате</b>\n\n"
    "Прикрепите файл PDF (скриншот из приложения банка → Сохранить как PDF).\n"
    "Изображения не принимаются — только PDF."
)

_ALREADY_PENDING = (
    "⏳ <b>Ваша заявка уже на проверке.</b>\n\n"
    "Ожидайте — администратор рассмотрит её в ближайшее время."
)

_ALREADY_APPROVED = (
    "✅ <b>Ваша оплата уже подтверждена!</b>\n\n"
    "У вас есть полный доступ к материалам."
)


# ── User handlers ─────────────────────────────────────────────────────────────

@router.message(F.text == "💳 Оплата")
async def show_payment_info(message: Message, state: FSMContext) -> None:
    await state.clear()

    # Check existing status
    status = await get_user_payment_status(message.from_user.id)
    if status == "approved":
        await message.answer(_ALREADY_APPROVED, parse_mode="HTML")
        return
    if status == "pending":
        await message.answer(_ALREADY_PENDING, parse_mode="HTML")
        return

    text = _PAYMENT_INFO.format(
        bank=PAYMENT_BANK,
        card=PAYMENT_CARD,
        recipient=PAYMENT_RECIPIENT,
        amount=PAYMENT_AMOUNT,
    )
    await message.answer(text, parse_mode="HTML")
    await message.answer(_WAIT_RECEIPT, parse_mode="HTML", reply_markup=cancel_payment_kb())
    await state.set_state(PaymentState.waiting_receipt)


@router.message(PaymentState.waiting_receipt, F.document)
async def handle_receipt(message: Message, state: FSMContext, bot: Bot) -> None:
    doc = message.document

    # Validate PDF
    is_pdf = (
        (doc.mime_type or "").lower() == "application/pdf"
        or (doc.file_name or "").lower().endswith(".pdf")
    )
    if not is_pdf:
        await message.answer(
            "❌ Нужен файл в формате <b>PDF</b>.\n"
            "Сохраните квитанцию из банковского приложения как PDF и отправьте снова.",
            parse_mode="HTML",
            reply_markup=cancel_payment_kb(),
        )
        return

    user = message.from_user
    payment_id = await create_payment(user.id, doc.file_id)

    # Build info line for admin
    mention = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    full_name = user.full_name or "—"

    admin_caption = (
        f"💳 <b>Новая заявка на оплату</b>  <code>#{payment_id}</code>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"🔗 <b>Контакт:</b> {mention}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n\n"
        "Проверьте чек и подтвердите или отклоните заявку."
    )

    try:
        await bot.send_document(
            chat_id=ADMIN_ID,
            document=doc.file_id,
            caption=admin_caption,
            parse_mode="HTML",
            reply_markup=admin_payment_kb(payment_id, user.id),
        )
    except Exception as exc:
        # Don't leave user hanging if admin notification fails
        await message.answer(
            "⚠️ Не удалось отправить чек администратору. Попробуйте позже.",
            parse_mode="HTML",
        )
        raise exc

    await state.clear()
    await message.answer(
        "✅ <b>Чек отправлен на проверку!</b>\n\n"
        "Администратор рассмотрит вашу заявку и вы получите уведомление о результате.\n"
        "Обычно это занимает до 24 часов.",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(PaymentState.waiting_receipt)
async def handle_receipt_wrong_type(message: Message) -> None:
    """Catch any non-document message while waiting for receipt."""
    await message.answer(
        "❌ Пожалуйста, отправьте файл <b>PDF</b> (не фото и не текст).\n\n"
        "Как получить PDF: откройте квитанцию в банковском приложении → "
        "«Поделиться» → «Сохранить как PDF» → отправьте файл сюда.",
        parse_mode="HTML",
        reply_markup=cancel_payment_kb(),
    )


@router.callback_query(F.data == "pay_cancel")
async def cancel_payment(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(
        "❌ Загрузка чека отменена. Возвращайтесь, когда будете готовы оплатить.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


# ── Admin callbacks ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_approve:"))
async def admin_approve(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    _, payment_id_str, user_id_str = callback.data.split(":")
    payment_id = int(payment_id_str)
    user_id = int(user_id_str)

    await update_payment_status(payment_id, "approved")

    # Notify user
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>Оплата подтверждена!</b>\n\n"
                "Ваш доступ к материалам активирован. Добро пожаловать!\n"
                "Нажмите «🎓 Уроки» чтобы начать обучение."
            ),
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        pass  # User may have blocked the bot

    # Update admin message — remove buttons, add status stamp
    new_caption = (callback.message.caption or "") + "\n\n✅ <b>ПОДТВЕРЖДЕНО</b>"
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML")
    except TelegramBadRequest:
        pass

    await callback.answer("✅ Доступ выдан пользователю!", show_alert=True)


@router.callback_query(F.data.startswith("pay_reject:"))
async def admin_reject(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    _, payment_id_str, user_id_str = callback.data.split(":")
    payment_id = int(payment_id_str)
    user_id = int(user_id_str)

    await update_payment_status(payment_id, "rejected")

    # Notify user
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>Оплата отклонена.</b>\n\n"
                "К сожалению, ваш чек не был принят.\n"
                "Пожалуйста, убедитесь, что:\n"
                "• сумма перевода верная\n"
                "• реквизиты правильные\n"
                "• файл читаемый и содержит подтверждение\n\n"
                "Попробуйте снова (кнопка «💳 Оплата») или свяжитесь с куратором."
            ),
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        pass

    # Update admin message
    new_caption = (callback.message.caption or "") + "\n\n❌ <b>ОТКЛОНЕНО</b>"
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML")
    except TelegramBadRequest:
        pass

    await callback.answer("❌ Заявка отклонена.", show_alert=True)
