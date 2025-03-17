from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from db_handler.db_class import (
    insert_data,
    get_user_products,
    is_product_already_in_db,
    delete_product,
    update_user_products_info,
)
from db_handler.models import User, Product
from prodcr import get_prod
from .find import is_valid_url
from .start import Mode

track_router = Router()

@track_router.message(F.text == "Посмотреть отслеживаемые товары", Mode.track_mode)
async def show_tracked_items(message: Message):
    products = await get_user_products(user_id=message.from_user.id)
    if products:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⏹Не отслеживать", callback_data="delete")]
            ]
        )
        for prod in products:
            product = get_prod(prod.url)
            current_price = product.price_with_card  # Новая цена с картой
            
            # Инициализируем флаг обновления
            update_data = {}

            # Обновляем текущую цену
            update_data['cur_price'] = current_price

            # Проверяем и обновляем максимальную цену
            if current_price > prod.max_price:
                update_data['max_price'] = current_price

            # Проверяем и обновляем минимальную цену
            if current_price < prod.min_price:
                update_data['min_price'] = current_price

            # Обновляем запись в базе данных, если есть изменения
            if update_data:
                await update_product(
                    product_id=prod.id,
                    **update_data
                )
            await message.answer(
                f"{product.name}\n{product.url}\nТекущая цен: {product.cur_price}\nМаксимальная цена: {prod.max_price}\nМинимальная цена: {prod.min_price}",
                reply_markup=keyboard,
            )
    else:
        await message.answer("На данный момент ни один товар не отслеживается")


@track_router.callback_query(F.data == "delete")
async def del_product(callback: Message, state):
    text = callback.message.text
    url = text.split("\n")[1]
    user_id = callback.from_user.id
    result = await delete_product(url, user_id)
    if result:
        await callback.message.delete()
        await callback.message.answer("Товар больше не отслеживается")
    else:
        await callback.message.answer(
            "При удалении произошла ошибка. Попробуйте позднее"
        )


@track_router.message(F.text == "Добавить товар", Mode.track_mode)
async def get_item_for_track(message: Message):
    await message.answer("Отправьте ссылку на товар, который желаете отслеживать")
        
        
@track_router.message(F.text.func(is_valid_url), Mode.track_mode)
async def get_item_for_track(message: Message):
    url = message.text
    if await is_product_already_in_db(url, message.from_user.id):
        await message.answer("Товар уже добавлен")
        return

    product = await get_prod(message.text)
    user_info = User(user_id=message.from_user.id, username=message.from_user.username)

    result = await insert_data(product, user_info)
    if result:
        await message.answer("Товар успешно добавлен")
        return
    await message.answer("Произошла ошибка при добавлении товара")

@track_router.message(Mode.track_mode)
async def get_item_for_track(message: Message):
    await message.answer("Необходимо ввести ссылку")
