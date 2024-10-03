import aiohttp
import json
import xml.etree.ElementTree as ET
import os
import gzip
from fastapi import HTTPException
from app.utils.utils import logger
from app.services.auth import auth_service
from app.config import settings
import asyncio
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

class WarehouseBalancesService:
    def __init__(self):
        self.base_url = settings.MY_SKLAD_API_URL
        self.stores = [
            "ROZETKA Фулфілмент",
            "Магазин",
            "Магазин MonkeyShop",
            "Основной склад",
            "Склад Victoria'S Secret",
            "Склад приёмки"
        ]

    async def get_warehouse_balances(self):
        """
        Получает данные об остатках по складам асинхронно.
        """
        endpoint = "report/stock/bystore"
        logger.info(f"Начало получения данных об остатках по складам для эндпоинта: {endpoint}")
        try:
            all_data = []
            offset = 0
            limit = 1000
            while True:
                url = f"{self.base_url}/{endpoint}?offset={offset}&limit={limit}"
                headers = await auth_service.get_auth_header()
                logger.info(f"Запрос к URL: {url}")

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            all_data.extend(data.get('rows', []))
                            logger.info(f"Получено {len(data.get('rows', []))} записей. Всего: {len(all_data)}")
                            if len(data.get('rows', [])) < limit:
                                break  # Все данные получены
                            offset += limit
                        elif response.status == 401:
                            logger.warning("Получен код 401, попытка обновления токена")
                            await auth_service.refresh_token()
                        else:
                            logger.error(f"Неожиданный код ответа: {response.status}")
                            raise HTTPException(status_code=response.status, detail="Ошибка при получении данных от API МойСклад")

            # Сохранение сырых данных в архив
            archive_path = os.path.join(settings.ARCHIVE_DIR, 'warehouse_balances_raw.gz')
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Сырые данные сохранены в архив: {archive_path}")

            # Обработка данных
            processed_data = await self.process_warehouse_balances(all_data)

            # Сохранение обработанных данных в JSON
            json_filename = os.path.join(settings.JSON_DIR, 'warehouse_balances.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Обработанные данные об остатках по складам сохранены в {json_filename}")

            # Сохранение в XML
            xml_filename = os.path.join(settings.XML_DIR, 'warehouse_balances.xml')
            self.save_to_xml(processed_data, xml_filename)
            logger.info(f"Данные сохранены в XML: {xml_filename}")

            return {
                "message": "Данные об остатках по складам успешно получены и обработаны",
                "count": len(processed_data),
                "archive_file": archive_path,
                "json_file": json_filename,
                "xml_file": xml_filename
            }
        except Exception as e:
            logger.error(f"Ошибка при получении данных об остатках по складам: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def extract_id_from_url(self, url):
        """
        Извлекает ID товара из URL.
        """
        parts = url.split('/')
        return parts[-1].split('?')[0]

    def process_item(self, item):
        """
        Обрабатывает отдельный элемент данных.
        """
        product_id = self.extract_id_from_url(item['meta']['href'])
        stores_with_stock = []

        for store_data in item.get('stockByStore', []):
            store_name = store_data.get('name', '')
            if store_name in self.stores and store_data.get('stock', 0) > 0:
                stores_with_stock.append(store_name)

        if stores_with_stock:
            return {
                'id': product_id,
                'store': ', '.join(stores_with_stock)
            }
        return None

    async def process_warehouse_balances(self, raw_data):
        """
        Обрабатывает сырые данные об остатках по складам с использованием многопроцессорной обработки.
        """
        logger.info("Начало обработки сырых данных об остатках по складам")

        # Определение количества процессоров
        num_processors = multiprocessing.cpu_count()
        logger.info(f"Используется {num_processors} процессоров для обработки")

        # Разделение данных на части для обработки
        chunk_size = len(raw_data) // num_processors
        chunks = [raw_data[i:i + chunk_size] for i in range(0, len(raw_data), chunk_size)]

        # Создание пула процессов
        with ProcessPoolExecutor(max_workers=num_processors) as executor:
            # Запуск обработки в нескольких процессах
            futures = [executor.submit(self.process_chunk, chunk) for chunk in chunks]

            # Сбор результатов
            processed_data = []
            for future in futures:
                processed_data.extend(future.result())

        logger.info(f"Обработка завершена. Обработано {len(processed_data)} элементов с ненулевыми остатками")
        return processed_data

    def process_chunk(self, chunk):
        """
        Обрабатывает часть данных в отдельном процессе.
        """
        return [self.process_item(item) for item in chunk if self.process_item(item)]

    def save_to_xml(self, data, filename):
        """
        Сохраняет данные в XML файл.
        """
        root = ET.Element('warehouse_balances')
        for item in data:
            product = ET.SubElement(root, 'product')
            for key, value in item.items():
                ET.SubElement(product, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

warehouse_balances_service = WarehouseBalancesService()
