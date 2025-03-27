from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

start_router = Router()


default_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Посмотреть отслеживаемые товары")]])

valid_names = ("ozon.ru", "wildberries.ru")


def get_default_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰Найти дешевле", callback_data="find_cheaper")],
        [InlineKeyboardButton(text="⤴Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="❌Отмена", callback_data="cancel")]
    ])


def is_valid_url(text: str) -> bool:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    finded_string = url_pattern.search(text)
    if not bool(finded_string):
        return False
    
    return any(name in text for name in valid_names)

async def get_url(text: str) -> str:
    url_pattern = re.compile(
        r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    )
    url = url_pattern.search(text).group(0)
    return url

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()', reply_markup=default_keyboard)
    
@start_router.message(Command("help"))
async def cmd_hep(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /help используя фильтр Command("help")')
    
@start_router.message(F.text.func(is_valid_url))
async def process_url(message: Message, state: FSMContext):
    url = await get_url(message.text)
    await state.clear()
    
    await message.answer(f"{url}", reply_markup=get_default_keyboard())
    
@start_router.callback_query(F.data == "cancel")
async def cancel(callback: Message, state:FSMContext):
    await callback.message.delete()
    await state.clear()