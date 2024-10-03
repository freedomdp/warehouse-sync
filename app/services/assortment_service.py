import aiohttp
import json
import xml.etree.ElementTree as ET
import os
import gzip
from fastapi import HTTPException
from app.utils.utils import logger
from app.services.auth import auth_service
from app.config import settings

class AssortmentService:
    def __init__(self):
        self.base_url = settings.MY_SKLAD_API_URL

    async def get_assortment(self):
        """
        Получает данные об ассортименте товаров асинхронно.
        """
        endpoint = "entity/assortment"
        logger.info(f"Начало получения данных об ассортименте для эндпоинта: {endpoint}")
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
            archive_path = os.path.join(settings.ARCHIVE_DIR, 'assortment_raw.gz')
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Сырые данные сохранены в архив: {archive_path}")

            # Обработка данных
            processed_data = self.process_assortment(all_data)

            # Сохранение обработанных данных в JSON
            json_filename = os.path.join(settings.JSON_DIR, 'assortment.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Обработанные данные об ассортименте сохранены в {json_filename}")

            # Сохранение в XML
            xml_filename = os.path.join(settings.XML_DIR, 'assortment.xml')
            self.save_to_xml(processed_data, xml_filename)
            logger.info(f"Данные сохранены в XML: {xml_filename}")

            return {
                "message": "Данные об ассортименте успешно получены и обработаны",
                "count": len(processed_data),
                "archive_file": archive_path,
                "json_file": json_filename,
                "xml_file": xml_filename
            }
        except Exception as e:
            logger.error(f"Ошибка при получении данных об ассортименте: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def extract_id_from_url(self, url):
        """
        Извлекает ID товара из URL.
        """
        parts = url.split('/')
        return parts[-1].split('?')[0]

    def process_assortment(self, raw_data):
        """
        Обрабатывает сырые данные об ассортименте.
        """
        logger.info("Начало обработки сырых данных об ассортименте")
        processed_data = []
        for item in raw_data:
            processed_item = {
                'id': self.extract_id_from_url(item['meta']['href']),  # Извлекаем ID из URL
                'article': item.get('article', ''),
                'code': item.get('code', ''),
                'description': item.get('description', ''),
                'externalCode': item.get('externalCode', ''),
                'name': item.get('name', ''),
                'pathname': item.get('pathName', ''),
                'stockStore': self.process_stock_stores(item.get('stockStore', [])),
                'updated': item.get('updated', '')
            }
            processed_data.append(processed_item)
        logger.info(f"Обработка завершена. Обработано {len(processed_data)} элементов ассортимента")
        return processed_data

    def process_stock_stores(self, stock_stores):
        """
        Обрабатывает информацию о складах, выбирая только те, где есть ненулевой остаток.
        """
        non_empty_stores = [store['name'] for store in stock_stores if store.get('stock', 0) > 0]
        return ', '.join(non_empty_stores)

    def save_to_xml(self, data, filename):
        """
        Сохраняет данные в XML файл.
        """
        root = ET.Element('assortment')
        for item in data:
            product = ET.SubElement(root, 'product')
            for key, value in item.items():
                ET.SubElement(product, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

assortment_service = AssortmentService()
