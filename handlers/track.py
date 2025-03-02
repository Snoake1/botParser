from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import re

from .start import Mode

track_router = Router()

@track_router.message(F.text == "Посмотреть отслеживаемые товары", Mode.track_mode)
async def show_tracked_items(message: Message):
    await message.answer("На данный момент ни один товар не отслеживается")


@track_router.message(F.text == "Добавить товар", Mode.track_mode)
async def show_tracked_items(message: Message):
    await message.answer("На данный момент ни один товар не отслеживается")