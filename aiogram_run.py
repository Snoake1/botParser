import asyncio
from create_bot import bot, dp
from handlers.start import start_router
from handlers.find import find_router
from handlers.track import track_router

async def main():
    # scheduler.add_job(send_time_msg, 'interval', seconds=10)
    # scheduler.start()
    dp.include_router(track_router)
    dp.include_router(find_router)
    dp.include_router(start_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())