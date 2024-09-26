import os
import json
import httpx
import asyncio
from app.services.sync.auth_service import AuthService
from app.utils.utils import logger
from app.config import settings

class DataRetrievalService:
    def __init__(self):
        self.auth_service = AuthService()
        self.base_url = f"{self.auth_service.base_url}/entity/product"
        self.output_file = settings.OUTPUT_FILE

    async def fetch_all_products(self):
        """
        Получение всех продуктов из API с учетом настроек.
        """
        logger.info("Начало получения всех продуктов")
        offset = 0
        total_products = 0

        # Очистка файла перед началом новой синхронизации
        with open(self.output_file, 'w') as f:
            json.dump([], f)

        while settings.TOTAL_PRODUCTS == 0 or total_products < settings.TOTAL_PRODUCTS:
            try:
                products = await self.fetch_products_batch(offset, settings.BATCH_SIZE)
                if not products:
                    break
                total_products += len(products)
                await self.save_products_to_file(products)
                logger.info(f"Получено и сохранено всего продуктов: {total_products}")
                if len(products) < settings.BATCH_SIZE or (settings.TOTAL_PRODUCTS > 0 and total_products >= settings.TOTAL_PRODUCTS):
                    break
                offset += len(products)
                await asyncio.sleep(settings.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"Ошибка при получении партии продуктов: {str(e)}")
                await asyncio.sleep(settings.REQUEST_DELAY)

        logger.info(f"Завершено получение всех продуктов. Всего получено: {total_products}")
        return total_products

    async def fetch_products_batch(self, offset, limit):
        """Получение партии продуктов из API."""
        auth_header = self.auth_service.get_auth_header()
        url = f"{self.base_url}?offset={offset}&limit={limit}"

        for attempt in range(3):  # Попробуем 3 раза
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=auth_header)
                    response.raise_for_status()
                    data = response.json()
                    return data.get('rows', [])  # Возвращаем полные данные о товарах
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1}/3 не удалась: {str(e)}")
                if attempt < 2:  # Если это не последняя попытка
                    await asyncio.sleep(settings.REQUEST_DELAY)
                else:
                    raise  # Если это была последняя попытка, поднимаем исключение

    async def save_products_to_file(self, products):
        """Сохранение продуктов в файл."""
        try:
            with open(self.output_file, 'r+') as f:
                file_data = json.load(f)
                file_data.extend(products)
                f.seek(0)
                json.dump(file_data, f, indent=2)
                f.truncate()
            logger.info(f"Сохранено {len(products)} продуктов в файл. Всего продуктов в файле: {len(file_data)}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении продуктов в файл: {str(e)}")
