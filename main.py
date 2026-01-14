import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
# Импортируем все хендлеры из папки handlers
from handlers import start, admin, shop, referrals

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # ПОРЯДОК ВАЖЕН: сначала админ, потом остальные
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(shop.router)      # Добавляем роутер магазина
    dp.include_router(referrals.router) # Добавляем роутер рефералов

    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")