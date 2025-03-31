import logging
import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from redis.asyncio import Redis

scheduler = AsyncIOScheduler(timezone=datetime.timezone.utc)
admins = [int(admin_id) for admin_id in config("ADMINS").split(",")]

REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = int(config("REDIS_PORT"))

redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
storage = RedisStorage(redis=redis)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=config("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)
