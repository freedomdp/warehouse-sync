import json
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import pytz
from fastapi import HTTPException
from app.utils.utils import logger
from app.config import settings
from app.services.assortment_service import assortment_service
from app.services.warehouse_stock_service import warehouse_stock_service
from app.services.warehouse_balances_service import warehouse_balances_service
from app.services.google_sheets_service import google_sheets_service

class ProductCollectorService:
    def __init__(self):
        self.json_dir = settings.JSON_DIR

    async def collect_and_process_data(self):
        """
        Собирает данные из всех источников, обрабатывает их и сохраняет в различных форматах.
        """
        logger.info("Начало сбора и обработки данных о товарах")
        result = {
            "message": "Данные частично обработаны",
            "steps_completed": [],
            "errors": []
        }
        try:
            # Шаг 1: Запуск эндпоинтов для обновления данных
            await assortment_service.get_assortment()
            await warehouse_stock_service.get_warehouse_stock()
            await warehouse_balances_service.get_warehouse_balances()
            result["steps_completed"].append("Data retrieval")

            # Шаг 2: Чтение и объединение данных
            assortment_data = self.read_json_file('assortment.json')
            warehouse_balances_data = self.read_json_file('warehouse_balances.json')
            warehouse_stock_data = self.read_json_file('warehouse_stock.json')

            combined_data = self.combine_data(assortment_data, warehouse_balances_data, warehouse_stock_data)
            result["steps_completed"].append("Data combination")

            # Шаг 3: Сохранение объединенных данных
            json_filename = os.path.join(settings.JSON_DIR, 'combined_products.json')
            self.save_to_json(combined_data, json_filename)

            xml_filename = os.path.join(settings.XML_DIR, 'combined_products.xml')
            self.save_to_xml(combined_data, xml_filename)
            result["steps_completed"].append("Data saving (JSON and XML)")

            # Шаг 4: Выгрузка в Google Sheets
            try:
                sheet_url = await google_sheets_service.upload_to_sheets(combined_data)
                result["steps_completed"].append("Google Sheets upload")
                result["google_sheet_url"] = sheet_url
            except Exception as e:
                logger.error(f"Ошибка при выгрузке в Google Sheets: {str(e)}", exc_info=True)
                result["errors"].append(f"Google Sheets upload failed: {str(e)}")

            result["message"] = "Данные успешно собраны и обработаны"
            result["json_file"] = json_filename
            result["xml_file"] = xml_filename
            result["total_products"] = len(combined_data)

            return result
        except Exception as e:
            logger.error(f"Ошибка при сборе и обработке данных: {str(e)}", exc_info=True)
            result["errors"].append(f"General error: {str(e)}")
            return result

    def read_json_file(self, filename):
        """Чтение JSON файла."""
        file_path = os.path.join(self.json_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def combine_data(self, assortment_data, warehouse_balances_data, warehouse_stock_data):
        """Объединение данных из разных источников."""
        combined_data = {}

        # Создаем словари для быстрого поиска
        balances_dict = {item['id']: item for item in warehouse_balances_data}
        stock_dict = {item['id']: item for item in warehouse_stock_data}

        for item in assortment_data:
            product_id = item['id']
            combined_item = {
                'id': product_id,
                'article': item.get('article', ''),
                'code': item.get('code', ''),
                'externalCode': item.get('externalCode', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'pathname': item.get('pathname', ''),
                'store': balances_dict.get(product_id, {}).get('store', ''),
                'salePrice': stock_dict.get(product_id, {}).get('salePrice', 0),
                'stock': stock_dict.get(product_id, {}).get('stock', 0),
                'updated': self.format_date(item.get('updated', ''))
            }
            combined_data[product_id] = combined_item

        return list(combined_data.values())

    def format_date(self, date_string):
        """Форматирование даты в нужный формат."""
        if not date_string:
            return ''
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        kiev_tz = pytz.timezone('Europe/Kiev')
        dt_kiev = dt.astimezone(kiev_tz)
        return dt_kiev.strftime('%d.%m.%y %H:%M')

    def save_to_json(self, data, filename):
        """Сохранение данных в JSON файл."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в JSON: {filename}")

    def save_to_xml(self, data, filename):
        """Сохранение данных в XML файл."""
        root = ET.Element('products')
        for item in data:
            product = ET.SubElement(root, 'product')
            for key, value in item.items():
                ET.SubElement(product, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        logger.info(f"Данные сохранены в XML: {filename}")

product_collector_service = ProductCollectorService()
