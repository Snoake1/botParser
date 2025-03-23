from decouple import config
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Product
from sqlalchemy.sql import func
from sqlalchemy import text

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
            if not user:
                status = await insert_user(user_info, session)
                if status:
                    print(f"Добавлен новый пользователь: {user_info.username}")
                else:
                    return "Не удалось добавить пользователя"
                status = await insert_product(product, user_info.user_id, session)
                return status
            else:
                user.last_active = func.now()
                status = await insert_product(product, user_info.user_id, session)
                return status
        return "Товар успешно добавлен"
        


async def insert_product(product, user_id, session) -> bool|str:
    try:
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


async def get_products():
    async with async_session() as session:
        async with session.begin(): 
            res = await session.execute(select(Product))
            return res.scalars().all()


async def is_product_already_in_db(url, user_id):
    results = await get_user_products(user_id)
    if any(url == p.url for p in results):
        return True
    return False


async def update_user_products_info(user_id):
    products = get_user_products(user_id)
    for product in products:
        products.url


async def delete_product(url, user_id):
    async with async_session() as session:
        async with session.begin():
            try:
                stmt = select(Product).where(
                    (Product.url == url) & 
                    (Product.user_id == user_id)
                )
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()

                if not product:
                    print("Продукт не найден")
                    return False

                await session.delete(product) 
                return True

            except Exception as e:
                print(f"Ошибка при удалении: {str(e)}")
                return False
        return True
  
    
async def update_product(product_id: int, **kwargs):
    async with async_session() as session:
        async with session.begin():
            # Получаем продукт
            stmt = select(Product).where(Product.product_id == product_id)
            result = await session.execute(stmt)
            product = result.scalar_one()

            # Обновляем поля
            for key, value in kwargs.items():
                setattr(product, key, value)

            # Добавляем в сессию и сохраняем
            session.add(product)


async def get_same_prod_from_db(name, similarity_threshold):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    """
                        SELECT * FROM products 
                        WHERE similarity(name, :name) > :threshold 
                        ORDER BY similarity(name, :name) DESC
                        """
                ),
                {"name": name, "threshold": similarity_threshold},
            )
            return result.fetchall()


if __name__ == "__main__":
    asyncio.run(init_db())
