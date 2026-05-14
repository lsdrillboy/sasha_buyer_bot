from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.kb import back_main_kb
from services.shipping import all_rates

router = Router()


def _build_text() -> str:
    rates = all_rates()
    lines = ["💰 <b>Тарифы доставки из Кореи</b>"]

    groups = [
        ("📦 До 5 кг",     lambda k: float(k) <= 5.0),
        ("📦 5–10 кг",     lambda k: 5.0 < float(k) <= 10.0),
        ("📦 10–20 кг",    lambda k: 10.0 < float(k) <= 20.0),
        ("📦 Свыше 20 кг", lambda k: float(k) > 20.0),
    ]

    for title, condition in groups:
        items = [(k, v) for k, v in rates.items() if condition(k)]
        if not items:
            continue
        lines.append(f"\n{title}")
        for k, v in sorted(items, key=lambda x: float(x[0])):
            won = f"{v:,}".replace(",", ".")
            lines.append(f"  {float(k):.2f} кг — {won} вон")

    return "\n".join(lines)


@router.message(F.text == "💰 Прайс отправки")
async def show_price_list(message: Message) -> None:
    await message.answer(_build_text(), parse_mode="HTML", reply_markup=back_main_kb())


@router.callback_query(F.data == "show:price_list")
async def show_price_list_cb(callback: CallbackQuery) -> None:
    await callback.message.answer(_build_text(), parse_mode="HTML", reply_markup=back_main_kb())
    await callback.answer()
