from aiogram import Router, F
from aiogram.types import Message
from db_handler.db_class import insert_user, insert_product, insert_data, get_user_products
from db_handler.models import User, Product
from prodcr import get_prod
from .find import is_valid_url
from .start import Mode

track_router = Router()

@track_router.message(F.text == "Посмотреть отслеживаемые товары", Mode.track_mode)
async def show_tracked_items(message: Message):
    products = await get_user_products(user_id=message.from_user.id)
    if products:
        for prod in products:
            await message.answer(f"""{prod.name}\n
                                     {prod.url}\n
                                     Текущая цена{prod.cur_price}\n
                                     Максимальная цена{prod.max_price}\n
                                     Минимальная цена{prod.min_price}\n""")
    else:  
        await message.answer("На данный момент ни один товар не отслеживается")


@track_router.message(F.text == "Добавить товар", Mode.track_mode)
async def get_item_for_track(message: Message):
    await message.answer("Отправьте ссылку на товар, который желаете отслеживать")
        
        
@track_router.message(F.text.func(is_valid_url), Mode.track_mode)
async def get_item_for_track(message: Message):
    product = await get_prod(message.text)
    user_info = User(
        user_id=message.from_user.id,
        username=message.from_user.username
    )
    result = await insert_data(product, user_info)
    await message.answer(result)

@track_router.message(Mode.track_mode)
async def get_item_for_track(message: Message):
    await message.answer("Необходимо ввести ссылку")