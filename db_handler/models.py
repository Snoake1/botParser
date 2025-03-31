from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Класс для объеденения"""


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(32))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с Products (один-ко-многим)
    products = relationship("Product", back_populates="user")


# Модель Products
class Product(Base):
    """Модель товара"""
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(512), nullable=False)
    name = Column(String(255))
    cur_price = Column(
        Numeric(15, 2)
    )  # Цена с картой, если есть возможность купить с картой
    max_price = Column(Numeric(15, 2))
    min_price = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с User (обратная)
    user = relationship("User", back_populates="products")
