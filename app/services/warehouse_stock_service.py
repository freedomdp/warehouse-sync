import aiohttp
import json
import xml.etree.ElementTree as ET
import os
import gzip
from fastapi import HTTPException
from app.utils.utils import logger
from app.services.auth import auth_service
from app.config import settings

class WarehouseStockService:
    """
    Сервис для работы с данными о складских запасах.
    """

    def __init__(self):
        """
        Инициализация сервиса.
        """
        self.base_url = settings.MY_SKLAD_API_URL

    async def get_warehouse_stock(self, filter_params=None):
        """
        Получает данные о складских запасах асинхронно, учитывая пагинацию.

        :param filter_params: Параметры фильтрации (опционально)
        :return: Обработанные данные о складских запасах
        """
        endpoint = "report/stock/all"
        logger.info(f"Начало получения данных о складских запасах для эндпоинта: {endpoint}")
        try:
            all_data = []
            offset = 0
            limit = 1000  # Максимальное количество записей, возвращаемых за один запрос

            while True:
                url = f"{self.base_url}/{endpoint}?offset={offset}&limit={limit}"
                if filter_params:
                    url += "&" + "&".join([f"{k}={v}" for k, v in filter_params.items()])

                headers = await auth_service.get_auth_header()
                logger.info(f"Запрос к URL: {url}")

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        logger.info(f"Код ответа: {response.status}")
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

            # Сохранение сырых данных
            raw_json_path = os.path.join(settings.JSON_DIR, 'warehouse_stock_raw.json')
            with open(raw_json_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Сырые данные сохранены: {raw_json_path}")

            # Сохранение архива
            archive_path = os.path.join(settings.ARCHIVE_DIR, 'warehouse_stock_raw.gz')
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Архив сохранен: {archive_path}")

            # Обработка данных
            processed_data = self.process_warehouse_stock(all_data)

            # Сохранение обработанных данных в JSON
            json_filename = os.path.join(settings.JSON_DIR, 'warehouse_stock.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Обработанные данные о складских запасах сохранены в {json_filename}")

            # Сохранение в XML
            xml_filename = os.path.join(settings.XML_DIR, 'warehouse_stock.xml')
            self.save_to_xml(processed_data, xml_filename)
            logger.info(f"Данные сохранены в XML: {xml_filename}")

            return {
                "message": "Данные о складских запасах успешно получены и обработаны",
                "count": len(processed_data),
                "raw_data_file": raw_json_path,
                "processed_data_file": json_filename,
                "xml_file": xml_filename,
                "archive_file": archive_path,
                "applied_filters": filter_params or {}
            }
        except Exception as e:
            logger.error(f"Ошибка при получении данных о складских запасах: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def extract_id_from_url(self, url):
        """
        Извлекает ID товара из URL.
        """
        parts = url.split('/')
        return parts[-1].split('?')[0]

    def process_warehouse_stock(self, raw_data):
        """
        Обрабатывает сырые данные о складских запасах.

        :param raw_data: Сырые данные
        :return: Обработанные данные
        """
        logger.info("Начало обработки сырых данных о складских запасах")
        processed_data = []
        for item in raw_data:
            try:
                processed_item = {
                    'id': self.extract_id_from_url(item['meta']['href']),  # ID товара
                    'name': item.get('name', ''),  # название товара
                    'code': item.get('code', ''),  # код товара
                    'article': item.get('article', ''),  # артикул товара
                    'salePrice': self.get_sale_price(item),  # стоимость товара
                    'stock': item.get('stock', 0),  # остаток товара на складе
                    'category': self.get_category(item),  # категория товара
                    'updated': item.get('updated', '')  # дата и время последнего обновления товара
                }
                processed_data.append(processed_item)
            except Exception as e:
                logger.error(f"Ошибка при обработке элемента: {str(e)}", exc_info=True)
                logger.error(f"Проблемный элемент: {item}")
        logger.info(f"Обработка завершена. Обработано {len(processed_data)} элементов складских запасов")
        return processed_data

    def get_sale_price(self, item):
        """
        Извлекает цену продажи из элемента.

        :param item: Элемент данных
        :return: Цена продажи в рублях
        """
        sale_price = item.get('salePrice')
        if isinstance(sale_price, dict):
            return sale_price.get('value', 0) / 100
        elif isinstance(sale_price, (int, float)):
            return sale_price / 100
        return 0

    def get_category(self, item):
        """
        Извлекает категорию товара из элемента.

        :param item: Элемент данных
        :return: Категория товара
        """
        folder = item.get('folder', {})
        if isinstance(folder, dict):
            # Сначала проверяем наличие и непустоту pathName
            path_name = folder.get('pathName')
            if path_name:
                return path_name

            # Если pathName отсутствует или пуст, используем name
            return folder.get('name', '')

        return ''

    def save_to_xml(self, data, filename):
        """
        Сохраняет данные в XML файл.

        :param data: Данные для сохранения
        :param filename: Имя файла для сохранения
        """
        root = ET.Element('warehouse_stock')
        for item in data:
            product = ET.SubElement(root, 'product')
            for key, value in item.items():
                ET.SubElement(product, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

warehouse_stock_service = WarehouseStockService()
