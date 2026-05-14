import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import (
    calculator, curator, faq, lessons, logistics,
    price_list, progress, start, suppliers,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main() -> None:
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Order matters: more specific text-filter handlers first
    dp.include_router(start.router)
    dp.include_router(lessons.router)
    dp.include_router(calculator.router)
    dp.include_router(price_list.router)
    dp.include_router(suppliers.router)
    dp.include_router(logistics.router)
    dp.include_router(faq.router)
    dp.include_router(curator.router)
    dp.include_router(progress.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
