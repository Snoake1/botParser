from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import re

from .start import Mode, track_keyboard, default_keyboard
from prodcr import find_cheaper_products

find_router = Router()

valid_names = ("ozon.ru", "wildberries.ru")

class Find(StatesGroup):
    cost_range = State()
    exact_match = State()


def get_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅Начать поиск", callback_data="find"),
            InlineKeyboardButton(text="🔍Точность поиска", callback_data="exact_match")
        ],
        [
            InlineKeyboardButton(text="💰Установить диапазон цен", callback_data="cost_range")
        ]
    ])



def is_valid_url(text: str) -> bool:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    finded_string = url_pattern.search(text)
    if not bool(finded_string):
        return False
    
    return any(name in text for name in valid_names)

def is_valid_range(text: str) -> bool:
    try:
        borders = text.split()
        return len(borders) == 2 and int(borders[0]) <= int(borders[1])
    except (ValueError, IndexError):
        return False


async def get_url(text: str) -> str:
    url_pattern = re.compile(
        r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    )
    url = url_pattern.search(text).group(0)
    return url


async def get_market(url: str) -> str:
    if "wildberries" in url:
        return "Wildberries"
    elif "ozon" in url:
        return "Ozon"
    else:
        return "Неизвестный сайт"


async def get_text(exact_match: bool = False, cost_range: str = "Не установлен") -> str:
    if cost_range == "Не установлен":
        range_text = "Не установлен"
    else:
        borders = cost_range.split()
        range_text = f"{borders[0]} - {borders[1]}"
    return (
        "Установленные параметры:\n\n"
        f"Точность поиска: {'✅Точное совпадение' if exact_match else '❌Не точный поиск'}\n"
        f"Диапазон цен: {range_text}\n\n"
        "Желаете установить дополнительные параметры поиска?"
    )
    

@find_router.message(F.text.func(is_valid_url), Mode.find_mode)
async def process_url(message: Message, state: FSMContext):
    url = await get_url(message.text)
    await state.clear()
    await state.set_data({
        'exact_match': False,
        'cost_range': "Не установлен",
        'url': url
    })
    
    await message.answer(await get_text(), reply_markup=get_keyboard())


@find_router.message(F.text == "Отслеживаемые товары", Mode.find_mode)
async def process_change_mode(message: Message, state: FSMContext):
    await message.answer("Вы можете отслеживать изменения цен на добавленные товары.", reply_markup=track_keyboard)
    await state.set_state(Mode.track_mode)



@find_router.message(Mode.find_mode)
async def process_text(message: Message, state: FSMContext):
    await message.answer(f'Не могу перейти по ссылке.\n\n'
                         f'Отправь ссылку на товар, и я постараюсь найти аналоги дешевле✨\n\n'
                         f'Доступные сайты:\n'
                         f'{"\n".join(valid_names)}')


@find_router.callback_query(F.data == "cost_range")
async def set_cost_range(callback: Message, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    if data.get('url') is None:
        await callback.message.answer("Сначала введите ссылку на товар.")
        return
    await callback.message.answer("Введите диапазон цен через пробел (например, 1000 5000):")
    await state.set_state(Find.cost_range)
    

@find_router.message(F.text, Find.cost_range)
async def process_cost_range(message: Message, state: FSMContext):
    if not re.match(r"^\d+ \d+$", message.text):
        await message.answer("Неверный формат. Введите диапазон цен через пробел")
        return
    if not is_valid_range(message.text):
        await message.answer("Неверный диапазон. Введите цены в порядке возрастания")
        return
    await state.update_data(cost_range=message.text)
    data = await state.get_data()
    await message.answer(await get_text(data.get('exact_match'), data.get('cost_range')), reply_markup=get_keyboard())


@find_router.callback_query(F.data == "exact_match")
async def set_exact_match(callback: Message, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    if not data.get('url'):
        await callback.message.answer("Сначала введите ссылку на товар.")
        return
    buttons = [
        [KeyboardButton(text="✅Точное совпадение"), KeyboardButton(text="❌Не точный поиск")]
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    await callback.message.answer("Выберите точность поиска:", reply_markup=keyboard)
    await state.set_state(Find.exact_match)


@find_router.message(Find.exact_match)
async def process_exact_match(message: Message, state: FSMContext):
    text = message.text
    if text == "✅Точное совпадение":
        await state.update_data(exact_match=True)
    elif text == "❌Не точный поиск":
        await state.update_data(exact_match=False)
    else:
        await message.answer("Пожалуйста, используйте кнопки на клавиатуре.")
        return
    data = await state.get_data()
    await message.answer("Точность установлена.", reply_markup=ReplyKeyboardRemove())
    await message.answer(await get_text(data['exact_match'], data['cost_range']), reply_markup=get_keyboard())

@find_router.callback_query(F.data == "find")
async def get_finding_params(callback: Message, state: FSMContext):
    data = await state.get_data()
    url = data.get('url')
    
    if not url:
        await callback.message.answer("Сначала введите ссылку на товар.")
        return
    await callback.message.delete()
    wait_msg = await callback.message.answer("Начинаю поиск. Это может занять некоторое время...")
    
    result = await find_cheaper_products(url, data.get('cost_range'), data.get('exact_match'))
    
    await wait_msg.delete()
    
    if isinstance(result, str):
        await callback.message.answer(result)
    else:
        for link, price in result.items():
            market = await get_market(link)
            await callback.message.answer(
                f"Цена: {price}\nМаркетплейс: {market}\n{link}"
            ,)
    await state.clear()
    await callback.answer(reply_markup=default_keyboard)
    
