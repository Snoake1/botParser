from aiogram import Router, F
from aiogram.types import Message
import re

from handlers.start import start_router
from seeker import find_cheaper_products
from asyncio import to_thread

find_router = Router()

def is_valid_url(text: str) -> bool:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return bool(url_pattern.match(text))

@find_router.message(F.text.func(is_valid_url))
async def find_cheaper(message: Message):
    await message.answer("Начинаю поиск...")
    result = await to_thread(find_cheaper_products, message.text)
    if result == "Нельзя парсить эту страницу":
        await message.answer("Не могу парсить эту страницу")
    else:
        await message.answer(result.__str__())

@find_router.message()
async def empty_request(message: Message):
    await message.answer("Введите ссылку на товар")