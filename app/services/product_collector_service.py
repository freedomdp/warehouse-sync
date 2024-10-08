import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from app.utils.utils import logger, load_json_file
from app.services.google_sheets_service import google_sheets_service
from app.config import settings
from app.routers.assortment import get_assortment
from app.routers.warehouse_balances import get_warehouse_balances
from app.routers.warehouse_stock import get_warehouse_stock

class ProductCollectorService:
    def __init__(self):
        self.json_dir = settings.JSON_DIR
        self.xml_dir = settings.XML_DIR

    def combine_data(self):
        logger.info("Начало объединения данных")
        combined_data = {}

        # Загрузка данных из файлов
        assortment_data = load_json_file(os.path.join(self.json_dir, 'assortment.json'))
        warehouse_stock_data = load_json_file(os.path.join(self.json_dir, 'warehouse_stock.json'))
        warehouse_balances_data = load_json_file(os.path.join(self.json_dir, 'warehouse_balances.json'))

        # Обработка данных ассортимента
        for item in assortment_data:
            if isinstance(item, dict) and 'id' in item:
                product_id = item['id']
                combined_data[product_id] = {
                    'id': product_id,
                    'article': item.get('article', ''),
                    'code': item.get('code', ''),
                    'externalCode': item.get('externalCode', ''),
                    'pathname': item.get('pathname', ''),
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'updated': item.get('updated', '')
                }

        # Добавление данных о складских запасах
        for item in warehouse_stock_data:
            if isinstance(item, dict) and 'id' in item:
                product_id = item['id']
                if product_id in combined_data:
                    combined_data[product_id]['salePrice'] = item.get('salePrice', '')
                    combined_data[product_id]['stock'] = item.get('stock', '')

        # Добавление данных об остатках по складам
        for item in warehouse_balances_data:
            if isinstance(item, dict) and 'id' in item:
                product_id = item['id']
                if product_id in combined_data:
                    combined_data[product_id]['store'] = item.get('store', '')

        logger.info(f"Объединено {len(combined_data)} записей")
        return list(combined_data.values())

    def merge_duplicate_products(self, combined_data):
        """
        Объединяет парные записи о товарах на основе поля 'code'.

        :param combined_data: Список словарей с данными о товарах
        :return: Список объединенных данных о товарах
        """
        # Создаем словарь для хранения товаров по коду
        products_by_code = {}

        # Проходим по всем товарам
        for product in combined_data:
            code = product.get('code')
            if code not in products_by_code:
                products_by_code[code] = []
            products_by_code[code].append(product)

        merged_products = []

        # Объединяем парные записи
        for code, products in products_by_code.items():
            if len(products) == 2:
                # Определяем, какая запись имеет значение в поле 'article'
                product_with_article = next((p for p in products if p.get('article')), None)
                product_without_article = next((p for p in products if not p.get('article')), None)

                if product_with_article and product_without_article:
                    # Объединяем данные
                    merged_product = {
                        'id': product_with_article['id'],
                        'article': product_with_article['article'],
                        'code': product_with_article['code'],
                        'externalCode': product_with_article['externalCode'],
                        'pathname': product_with_article['pathname'],
                        'name': product_with_article['name'],
                        'description': product_with_article['description'],
                        'salePrice': product_without_article.get('salePrice', ''),
                        'store': product_without_article.get('store', ''),
                        'stock': product_without_article.get('stock', ''),
                        'updated': product_with_article['updated']
                    }
                    merged_products.append(merged_product)
                else:
                    # Если не удалось определить пару, добавляем оба продукта
                    merged_products.extend(products)
            else:
                # Если нет пары, добавляем продукт как есть
                merged_products.extend(products)

        logger.info(f"Объединено {len(combined_data) - len(merged_products)} пар товаров")
        return merged_products

    async def collect_and_process_data(self):
        logger.info("Начало сбора и обработки данных о товарах")
        result = {
            "message": "Данные частично обработаны",
            "steps_completed": [],
            "errors": [],
            "warnings": []
        }

        try:
            # Обновление данных через соответствующие эндпоинты
            await get_assortment()
            result["steps_completed"].append("Assortment data update")

            await get_warehouse_balances()
            result["steps_completed"].append("Warehouse balances data update")

            await get_warehouse_stock()
            result["steps_completed"].append("Warehouse stock data update")

            # Объединение данных
            combined_data = self.combine_data()
            result["steps_completed"].append("Data combination")
            logger.info(f"Объединено {len(combined_data)} записей")

            merged_data = self.merge_duplicate_products(combined_data)
            result["steps_completed"].append("Duplicate products merged")
            logger.info(f"После объединения дубликатов осталось {len(merged_data)} записей")

            if not merged_data:
                result["warnings"].append("No data after merging duplicates")

            json_filename = os.path.join(self.json_dir, 'combined_products.json')
            self.save_to_json(merged_data, json_filename)
            xml_filename = os.path.join(self.xml_dir, 'combined_products.xml')
            self.save_to_xml(merged_data, xml_filename)
            result["steps_completed"].append("Data saving (JSON and XML)")

            if merged_data:
                try:
                    sheet_url = await google_sheets_service.upload_to_sheets(merged_data)
                    result["steps_completed"].append("Google Sheets upload")
                    result["google_sheet_url"] = sheet_url
                except Exception as e:
                    logger.error(f"Ошибка при выгрузке в Google Sheets: {str(e)}", exc_info=True)
                    result["errors"].append(f"Google Sheets upload failed: {str(e)}")
            else:
                result["warnings"].append("Skipping Google Sheets upload due to empty data")

            result["message"] = "Данные успешно собраны, обработаны и объединены"
            result["json_file"] = json_filename
            result["xml_file"] = xml_filename
            result["total_products"] = len(merged_data)
        except Exception as e:
            logger.error(f"Ошибка при сборе и обработке данных: {str(e)}", exc_info=True)
            result["errors"].append(f"General error: {str(e)}")

        return result

    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в JSON: {filename}")

    def save_to_xml(self, data, filename):
        root = ET.Element('products')
        for item in data:
            product = ET.SubElement(root, 'product')
            for key, value in item.items():
                ET.SubElement(product, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        logger.info(f"Данные сохранены в XML: {filename}")

product_collector_service = ProductCollectorService()
