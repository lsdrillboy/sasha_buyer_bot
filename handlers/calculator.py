from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from keyboards.kb import calc_result_kb
from services.currency import get_rates
from services.shipping import calculate

router = Router()


class CalcState(StatesGroup):
    waiting_weight = State()


def _fmt(n: float) -> str:
    """Format number with dots as thousands separator (Russian style)."""
    return f"{n:,.0f}".replace(",", ".")


@router.message(F.text == "📦 Калькулятор доставки")
async def start_calc(message: Message, state: FSMContext) -> None:
    await state.set_state(CalcState.waiting_weight)
    await message.answer(
        "📦 <b>Калькулятор доставки</b>\n\n"
        "Введите вес посылки в кг:\n"
        "<i>Пример: 2.3 или 7.5</i>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "calc:new")
async def new_calc(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CalcState.waiting_weight)
    await callback.message.answer(
        "📦 Введите вес посылки в кг <i>(например: 2.3)</i>:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CalcState.waiting_weight)
async def process_weight(message: Message, state: FSMContext) -> None:
    raw = message.text.replace(",", ".").strip()
    try:
        weight = float(raw)
        if not (0 < weight <= 100):
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректный вес, например: <code>2.3</code>",
            parse_mode="HTML",
        )
        return

    result = calculate(weight)
    if result is None:
        await message.answer("❌ Вес превышает максимальный тариф. Уточните стоимость у куратора.")
        await state.clear()
        return

    rate_key, krw = result
    rate_val = float(rate_key)
    rates = await get_rates()
    rub = krw * rates["RUB"]
    usd = krw * rates["USD"]

    lines = [
        f"📦 Вес: <b>{weight} кг</b>  (тариф для {rate_val} кг)",
        f"💰 Стоимость доставки: <b>{_fmt(krw)} вон</b>",
    ]
    if rub > 0:
        lines.append(f"≈ <b>{_fmt(rub)} ₽</b>")
    if usd > 0:
        lines.append(f"≈ <b>{usd:.1f} $</b>")
    if rub > 0 or usd > 0:
        lines.append("\n<i>Курс обновляется раз в сутки</i>")

    await state.clear()
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=calc_result_kb())
