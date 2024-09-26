# Сервис для обработки полученных данных

import json
from app.models.product import Product
from app.config.field_mapping import map_product
from app.utils.utils import logger
from app.config import settings
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

class DataProcessingService:
    async def process_products(self, session: AsyncSession):
        """
        Обработка продуктов и сохранение их в базу данных.
        """
        logger.info("Начало обработки продуктов")
        try:
            with open(settings.OUTPUT_FILE, 'r') as f:
                products_data = json.load(f)

            for product_data in products_data:
                mapped_product = map_product(product_data)
                await self.save_or_update_product(session, mapped_product)

            await session.commit()
            logger.info(f"Обработано и сохранено в базу данных {len(products_data)} продуктов")
        except Exception as e:
            logger.error(f"Ошибка при обработке продуктов: {str(e)}")
            await session.rollback()
            raise

    async def save_or_update_product(self, session: AsyncSession, product_data: dict):
        """
        Сохранение или обновление продукта в базе данных.
        """
        result = await session.execute(select(Product).where(Product.external_id == product_data['external_id']))
        existing_product = result.scalars().first()

        if existing_product:
            for key, value in product_data.items():
                setattr(existing_product, key, value)
        else:
            new_product = Product(**product_data)
            session.add(new_product)
