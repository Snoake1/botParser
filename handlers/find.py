import re
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from handlers.start import default_keyboard, get_url
from create_bot import bot
from producer import find_cheaper_products
from db_handler.db_handlers import get_same_prod_from_db

find_router = Router()

valid_names = ("ozon.ru", "wildberries.ru")


class Find(StatesGroup):
    cost_range = State()
    exact_match = State()


def get_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настройки поиска товаров"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅Начать поиск", callback_data="find"),
                InlineKeyboardButton(
                    text="🔍Точность поиска", callback_data="exact_match"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰Установить диапазон цен", callback_data="cost_range"
                )
            ],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )


def is_valid_range(text: str) -> bool:
    """Проверка диапазона цен"""
    try:
        borders = text.split()
        return (
            len(borders) == 2
            and int(borders[0]) <= int(borders[1])
            and int(borders[0]) > 0
        )
    except (ValueError, IndexError):
        return False


async def get_market(url: str) -> str:
    """Определение сайта"""
    if "wildberries" in url:
        return "Wildberries"
    if "ozon" in url:
        return "Ozon"
    return "Неизвестный сайт"


async def get_text(exact_match: bool = False, cost_range: str = "Не установлен") -> str:
    """Информация о текущих настройках для поиска товаров"""
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


@find_router.callback_query(F.data == "find_cheaper")
async def set_params_for_url(callback: Message, state: FSMContext):
    """ОБработка сообщения с url адрессом"""
    url = await get_url(callback.message.text)
    await callback.message.delete()
    await state.set_data(
        {"exact_match": False, "cost_range": "Не установлен", "url": url}
    )

    await callback.message.answer(await get_text(), reply_markup=get_keyboard())


@find_router.callback_query(F.data == "cost_range")
async def set_cost_range(callback: Message, state: FSMContext):
    """ОБработка нажатия кнопки установки диапазона"""
    await callback.message.delete()
    data = await state.get_data()
    if data.get("url") is None:
        await callback.message.answer("Сначала введите ссылку на товар.")
        return
    await callback.message.answer(
        "Введите диапазон цен через пробел (например, 1000 5000):"
    )
    await state.set_state(Find.cost_range)


@find_router.message(F.text, Find.cost_range)
async def process_cost_range(message: Message, state: FSMContext):
    """Установка диапазона цен"""
    if not re.match(r"^\d+ \d+$", message.text):
        await message.answer("Неверный формат. Введите диапазон цен через пробел")
        return
    if not is_valid_range(message.text):
        await message.answer("Неверный диапазон. Введите цены в порядке возрастания")
        return
    await state.update_data(cost_range=message.text)
    data = await state.get_data()
    await message.answer(
        await get_text(data.get("exact_match"), data.get("cost_range")),
        reply_markup=get_keyboard(),
    )


@find_router.callback_query(F.data == "exact_match")
async def set_exact_match(callback: Message, state: FSMContext):
    "Обработка нажатия на кнопку точности поиска"
    await callback.message.delete()
    data = await state.get_data()
    if not data.get("url"):
        await callback.message.answer("Сначала введите ссылку на товар.")
        return
    buttons = [
        [
            KeyboardButton(text="✅Точное совпадение"),
            KeyboardButton(text="❌Не точный поиск"),
        ]
    ]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    await callback.message.answer("Выберите точность поиска:", reply_markup=keyboard)
    await state.set_state(Find.exact_match)


@find_router.message(Find.exact_match)
async def process_exact_match(message: Message, state: FSMContext):
    "Установка точности совпадения"
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
    await message.answer(
        await get_text(data["exact_match"], data["cost_range"]),
        reply_markup=get_keyboard(),
    )


@find_router.callback_query(F.data == "find")
async def find_same_productss(callback: Message, state: FSMContext):
    """Обработка кнопки "Начать поиск"""
    data = await state.get_data()
    url = data.get("url")

    if not url:
        await callback.message.answer("Сначала введите ссылку на товар.")
        return

    await callback.message.delete()
    wait_msg = await callback.message.answer(
        "Начинаю поиск. Это может занять некоторое время..."
    )

    await state.clear()

    name, result = await find_cheaper_products(
        url, data.get("cost_range"), data.get("exact_match")
    )

    familiar_products = await get_same_prod_from_db(name)
    print(familiar_products)
    await wait_msg.delete()
    if familiar_products:
        await callback.message.answer("Пользователи выбирают:")

        for prod in familiar_products:
            await callback.message.answer(f"Цена: {prod.cur_price}\nСсылка: {prod.url}")

    if isinstance(result, str):
        await callback.message.answer(result, reply_markup=default_keyboard)
    else:
        await callback.message.answer("Найденные товары:")
        res = list(result.items())
        for link, price in res[:10]:
            market = await get_market(link)
            await callback.message.answer(
                f"Цена: {price}\nМаркетплейс: {market}\n{link}"
            )
        await bot.send_message(
            callback.from_user.id,
            "Это самые дешевые товары, что удалось найти",
            reply_markup=default_keyboard,
        )
