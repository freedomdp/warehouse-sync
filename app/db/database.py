# Файл, содержащий конфигурацию базы данных и основные функции для работы с ней

import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from app.config import settings
from app.utils.utils import logger
from app.models.product import Product
from app.config.field_mapping import map_product

# Создание базового класса для ORM-моделей
Base = declarative_base()

# Создание асинхронного движка базы данных
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("mysql://", "mysql+aiomysql://"),
    echo=False
)

# Создание фабрики сессий для асинхронной работы с базой данных
async_session = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session():
    """
    Функция-генератор для получения асинхронной сессии базы данных.
    """
    async with async_session() as session:
        yield session

async def create_tables():
    """
    Функция для создания таблиц в базе данных на основе определенных моделей.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def transfer_products_to_db():
    """
    Функция для переноса данных о продуктах в базу данных.
    """
    try:
        with open(settings.OUTPUT_FILE, 'r') as f:
            products_data = json.load(f)

        async with async_session() as session:
            for product_data in products_data:
                # Проверяем, существует ли продукт с таким external_id
                result = await session.execute(select(Product).where(Product.external_id == product_data['external_id']))
                existing_product = result.scalars().first()

                if existing_product:
                    # Обновляем существующий продукт
                    existing_product.name = product_data['name']
                    existing_product.price = product_data['price']
                    existing_product.updated_at = product_data['updated_at']
                else:
                    # Создаем новый продукт
                    new_product = Product(**product_data)
                    session.add(new_product)

            await session.commit()

        logger.info(f"Перенесено {len(products_data)} товаров в базу данных")
    except Exception as e:
        logger.error(f"Ошибка при переносе товаров в базу данных: {str(e)}")
        raise
