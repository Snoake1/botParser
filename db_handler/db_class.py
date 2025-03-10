from decouple import config
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Product
from sqlalchemy.sql import func

engine = create_async_engine(
    f"{config('PG_LINK')}",
    echo=True  # Включает логи SQL-запросов для отладки
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Функция создания таблиц
async def init_db():
    async with engine.begin() as conn:
        # Удаление таблиц (для тестирования, уберите в продакшене)
        await conn.run_sync(Base.metadata.drop_all)
        # Создание таблиц
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы.")
    
    
async def insert_data(product, user_info: User):
    async with async_session() as session:
        async with session.begin():
            user = await session.get(User, user_info.user_id)
            if user is None:
                status = await insert_user(user_info, session)
                if status:
                    print(f"Добавлен новый пользователь: {user_info.username}")
                else:
                    return "Не удалось добавить пользователя"
                status = await insert_product(product, user_info.user_id, session) #TODO test if prod exist
                if status == "Данный товар уже добавлен":
                    return status
                else:
                    return "Не удалось добавить товар"
            else:
                user.last_active = func.now()
                status = await insert_product(product, user_info.user_id, session)
                if status == "Данный товар уже добавлен":
                    return status
                else:
                    return "Не удалось добавить товар"
        await session.commit()
        return "Товар успешно добавлен"
        


async def insert_product(product, user_id, session) -> bool|str:
    try:
        results = await get_user_products(user_id)
        if any(product.name == p.name for p in results):
            return "Данный товар уже добавлен"
        product = Product(
                user_id=user_id,
                url=product.url,
                name=product.name,
                cur_price=product.price_with_card,
                max_price=product.price_with_card,
                min_price=product.price_with_card
            )
        session.add(product)
    except Exception as e:
        print(e)
        return False
    return True
        
        
async def insert_user(user_info: User, session):
    try:
        user = User(
                    user_id=user_info.user_id,
                    username=user_info.username,
                    )
        session.add(user)
    except:
        return False
    return True


async def get_user_products(user_id: int):
    async with async_session() as session:
        async with session.begin():
            stmt = select(Product).where(Product.user_id == user_id)
            result = await session.execute(stmt)
            products = result.scalars().all()
            return products if products else []


if __name__ == "__main__":
    asyncio.run(init_db())