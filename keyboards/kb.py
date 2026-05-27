from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="🎓 Уроки")
    b.button(text="📦 Калькулятор доставки")
    b.button(text="🏪 Поставщики")
    b.button(text="🚚 Логистика и отправка")
    b.button(text="❓ FAQ / Памятки")
    b.button(text="📞 Связаться с куратором")
    b.button(text="⚙️ Мой прогресс")
    b.button(text="💳 Оплата")
    b.adjust(2, 2, 2, 2)
    return b.as_markup(resize_keyboard=True)


def lessons_list_kb(lessons: list[dict], completed: list[int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for lesson in lessons:
        mark = "✅" if lesson["id"] in completed else "📖"
        num = lesson.get("number", str(lesson["id"]))
        b.button(
            text=f"{mark} Урок {num}: {lesson['title']}",
            callback_data=f"lesson:{lesson['id']}",
        )
    b.adjust(1)
    return b.as_markup()


def lesson_kb(lesson: dict, completed: list[int], next_num: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lid = lesson["id"]

    is_done = lid in completed
    b.button(
        text="✅ Выполнено" if is_done else "✔️ Отметить выполненным",
        callback_data=f"lesson_done:{lid}",
    )
    if lesson.get("next_lesson"):
        label = next_num or str(lesson["next_lesson"])
        b.button(
            text=f"➡️ Урок {label}",
            callback_data=f"lesson:{lesson['next_lesson']}",
        )
    b.button(text="⬅️ К урокам", callback_data="back:lessons")
    b.adjust(1)
    return b.as_markup()


def calc_result_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💰 Полный прайс", callback_data="show:price_list")
    b.button(text="🔄 Новый расчёт", callback_data="calc:new")
    b.adjust(2)
    return b.as_markup()


def faq_list_kb(items: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in items:
        b.button(
            text=f"{item['icon']} {item['title']}",
            callback_data=f"faq:{item['id']}",
        )
    b.adjust(1)
    return b.as_markup()


def back_faq_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К памяткам", callback_data="back:faq")
    return b.as_markup()


def back_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ В главное меню", callback_data="back:main")
    return b.as_markup()


def admin_payment_kb(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for admin: approve or reject a payment."""
    b = InlineKeyboardBuilder()
    b.button(
        text="✅ Подтвердить",
        callback_data=f"pay_approve:{payment_id}:{user_id}",
    )
    b.button(
        text="❌ Отклонить",
        callback_data=f"pay_reject:{payment_id}:{user_id}",
    )
    b.adjust(2)
    return b.as_markup()


def cancel_payment_kb() -> InlineKeyboardMarkup:
    """Cancel button shown during payment flow."""
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отменить", callback_data="pay_cancel")
    return b.as_markup()
