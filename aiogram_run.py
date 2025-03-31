import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from create_bot import bot, dp
from handlers.start import start_router
from handlers.find import find_router
from handlers.track import track_router
from handlers.track import send_update_price_message

scheduler = AsyncIOScheduler()


async def main():
    """
    Запуск бота
    """
    # scheduler.add_job(send_update_price_message, "interval", minutes=1)  # debug
    # Отправка каждый день в 18:00
    scheduler.add_job(send_update_price_message, "cron", hour=18, minute=0)
    scheduler.start()

    dp.include_router(track_router)
    dp.include_router(find_router)
    dp.include_router(start_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
