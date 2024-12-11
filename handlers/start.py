from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

start_router = Router()

available_shops = f'Озон\n' \
                   f'Wildberries'

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()')
    
@start_router.message(Command("help"))
async def cmd_hep(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запуск сообщения по команде /help используя фильтр Command("help")')

@start_router.message(F.text)
async def any_text(message: Message, state: FSMContext):
    await message.answer(f'К сожалению, я не понимаю.\n\n'
                         f'Отправь ссылку на товар, и я найду аналоги дешевле✨\n\n'
                         f'Доступные сайты:\n'
                         f'{available_shops}')