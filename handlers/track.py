from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from start import default_keyboard
from botSeeker.db_handler.models import User
from botSeeker.db_handler.db_class import (
    insert_data,
    get_user_products,
    is_product_already_in_db,
    delete_product,
    update_product,
    get_products,
)
from botSeeker.producer import get_prod
from botSeeker.create_bot import bot

track_router = Router()

prod_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏹Не отслеживать", callback_data="delete")]
    ]
)


async def send_update_price_message():
    """Функция отправки сообщения при обновления цены на товар"""
    products = await get_products()
    for db_prod in products:
        data_to_upd = {}
        new_prod = await get_prod(db_prod.url)

        if db_prod.cur_price != new_prod.price_with_card:
            diff = abs(new_prod.price_with_card - float(db_prod.cur_price))
            data_to_upd["cur_price"] = new_prod.price_with_card
            is_greater = True

            if new_prod.price_with_card > db_prod.max_price:
                data_to_upd["max_price"] = new_prod.price_with_card
                is_greater = True

            if new_prod.price_with_card < db_prod.min_price:
                data_to_upd["min_price"] = new_prod.price_with_card
                is_greater = False

            # Обновляем запись в базе данных, если есть изменения
            await update_product(product_id=db_prod.product_id, **data_to_upd)
            max_price = db_prod.max_price
            min_price = db_prod.min_price
            if is_greater:
                sticker = "📈"
                txt = "увеличилась на"
                max_price = new_prod.price_with_card
            else:
                sticker = "📉"
                txt = "уменьшилась на"
                min_price = new_prod.price_with_card
            text = f"{sticker}{db_prod.name}\n{db_prod.url}\nЦена на товар {txt} {diff}₽\n\
                Текущая цена:{new_prod.price_with_card}0₽\n\
                Максимальная цена:{max_price}₽\nМинимальная цена:{min_price}₽"
            await bot.send_message(db_prod.user_id, text, reply_markup=prod_keyboard)
    return


@track_router.message(F.text == "Посмотреть отслеживаемые товары")
async def show_tracked_items(message: Message):
    """Обработчик отслеживания товаров"""
    await message.answer("Почти вспомнили какие товары вы отслеживаете...")
    products = await get_user_products(user_id=message.from_user.id)
    if products:
        for prod in products:
            await message.answer(
                f"{prod.name}\n{prod.url}\nТекущая цена: {prod.cur_price}₽\n\
                    Максимальная цена: {prod.max_price}₽\nМинимальная цена: {prod.min_price}₽",
                reply_markup=prod_keyboard,
            )
    else:
        await message.answer("На данный момент ни один товар не отслеживается")


@track_router.callback_query(F.data == "delete")
async def del_product(callback: Message):
    """Обработчик удаления товара"""
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


@track_router.callback_query(F.data == "add_product")
async def get_item_for_track(callback: Message):
    """Обработчик добавления товара"""
    url = callback.message.text
    user_id = callback.from_user.id
    await callback.message.answer(f"Операция выполняется...{user_id}")

    if await is_product_already_in_db(url, user_id):
        await callback.message.answer(
            "Товар уже добавлен", reply_markup=default_keyboard
        )
        return

    product = await get_prod(url)
    user_info = User(user_id=user_id, username=callback.from_user.username)
    result = await insert_data(product, user_info)

    if result:
        await callback.message.answer("Товар успешно добавлен")
        return
    await callback.message.answer("Произошла ошибка при добавлении товара")
