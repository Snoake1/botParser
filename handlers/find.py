from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import re

from prodcr import find_cheaper_products

find_router = Router()



class Find(StatesGroup):
    cost_range = State()
    exact_match = State()

def get_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅Начать поиск", callback_data="find"),
            InlineKeyboardButton(text="🔍Точность поиска", callback_data="exact_match")
        ],
        [
            InlineKeyboardButton(text="💰Установить диапазон цен", callback_data="cost_range")
        ]
    ])
    return keyboard



def is_valid_url(text: str) -> bool:
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    finded_string = url_pattern.search(text)
    return bool(finded_string)


def is_valid_range(text: str) -> bool:
    borders = text.split()
    if int(borders[0]) > int(borders[1]):
        return False
    return True


async def get_url(text: str) -> str:
    url_pattern = re.compile(
        r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    )
    url = url_pattern.search(text).group(0)
    return url

async def get_link_kb(url: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Перейти", url=url, callback_data="goto"),
        ]
    ])
    return keyboard


async def get_market(url: str) -> str:
    if "wildberries" in url:
        return "Wildberries"
    elif "ozon" in url:
        return "Ozon"
    else:
        return "Неизвестный сайт"


async def get_text(exact_match: bool = False, cost_range: str="Не установлен") -> str:
    borders = cost_range.split()
    return f"Установленные параметы:\n\n" \
            f"Точность поиска: {"✅Точное совпадение" if exact_match else "Не точный поиск"}\n\n" \
            f"Диапозон цен: {borders[0]} {borders[1]}\n\n" \
            f"Желаете установить дополнительные параметры поиска?"



@find_router.message(F.text.func(is_valid_url))
async def get_finding_params(message: Message, state: FSMContext):
    url = await get_url(message.text)
    await state.clear()
    await state.set_data({
        'exact_match': False,
        'cost_range': "Не установлен",
        'url': url
    })
    
    await message.answer(await get_text(), reply_markup=get_keyboard())


@find_router.callback_query(F.data == "cost_range")
async def get_finding_params(callback: Message, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    if data.get('url') is None:
        await callback.message.answer("Введите ссылку на товар")
        return
    await callback.message.answer("Введите диапазон цен через пробел")
    await state.set_state(Find.cost_range)
    

@find_router.message(F.text, Find.cost_range)
async def get_finding_params(message: Message, state: FSMContext):
    if not re.match(r"^\d+ \d+$", message.text):
        await message.answer("Неверный формат диапазона цен. Введите диапазон цен через пробел")
        return
    if not is_valid_range(message.text):
        await message.answer("Неверный диапазон цен. Введите цены в порядке возрастания")
        return
    await state.update_data(cost_range=message.text)
    data = await state.get_data()
    await message.answer(await get_text(data.get('exact_match'), data.get('cost_range')), reply_markup=get_keyboard())


@find_router.callback_query(F.data == "exact_match")
async def get_finding_params(callback: Message, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Find.exact_match)
    
    data = await state.get_data()
    if data.get('url') is None:
        await callback.message.answer("Введите ссылку на товар")
        return
    
    buttons = [
        [KeyboardButton(text="✅Точное совпадение"), KeyboardButton(text="❌Не точный поиск")]
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    
    await callback.message.answer("Выберите точность поиска", reply_markup=keyboard)


@find_router.message(Find.exact_match)
async def get_finding_params(message: Message, state: FSMContext):
    
    if message.text == "✅Точное совпадение":
        await state.update_data(exact_match=True)
    elif message.text == "❌Не точный поиск":
        await state.update_data(exact_match=False)
    else:
        await message.answer("Воспользутейсь встроенной клавиатурой")
        return
    await message.answer("Точность установлена", reply_markup=ReplyKeyboardRemove())
    
    data = await state.get_data()
    await message.answer(await get_text(data.get('exact_match'), data.get('cost_range')), reply_markup=get_keyboard())


@find_router.callback_query(F.data == "find")
async def get_finding_params(callback: Message, state: FSMContext):
    data = await state.get_data()
    url = data.get('url')
    
    if url is None:
        await callback.message.answer("Введите ссылку на товар")
        return
    await callback.message.delete()
    await callback.message.answer("Начинаю поиск. Это может занять некоторое время...")
    await state.clear()
    result = find_cheaper_products(url, data.get('cost_range'), data.get('exact_match'))
    if type(result) == str:
        await callback.message.answer(result)
        return 
    
    for item in result.items():
        await callback.message.answer(f"Цена: {item[1]}\nМаркетплейс: {await get_market(item[0])}", reply_markup= await get_link_kb(item[0]))


@find_router.callback_query(F.data == "goto")
async def get_finding_params(callback: Message, state: FSMContext):
    await state.clear()
    url = callback.message.reply_markup.inline_keyboard[0][0].url
    await callback.message.answer(f"вы выбрали эту ссылку:{url}")
