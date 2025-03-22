from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

start_router = Router()


class Mode(StatesGroup):
    find_mode = State()
    track_mode = State()

default_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Найти дешевле"), KeyboardButton(text="Отслеживаемые товары")]])

track_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Посмотреть отслеживаемые товары"), KeyboardButton(text="Добавить товар")],
                                                                      [KeyboardButton(text="Найти дешевле")]])


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()', reply_markup=default_keyboard)
    
@start_router.message(Command("help"))
async def cmd_hep(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /help используя фильтр Command("help")')


@start_router.message(F.text == "Найти дешевле")
async def find_mode(message:Message, state:FSMContext):
    await message.answer("Отправьте ссылку на товар.\nЯ постараюсь предложить более выгодный вариант.", reply_markup=default_keyboard)
    await state.set_state(Mode.find_mode)
    
    
@start_router.message(F.text == "Отслеживаемые товары")
async def find_mode(message:Message, state:FSMContext):
    await message.answer("Вы можете отслеживать изменения цен на добавленные товары.", reply_markup=track_keyboard)
    await state.set_state(Mode.track_mode)