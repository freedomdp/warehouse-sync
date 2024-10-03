import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from app.config import settings

def process_and_clean_data(input_file, output_file):
    """
    Обрабатывает сырые данные о товарах и сохраняет только нужную информацию.
    """
    with open(input_file, 'r') as f:
        raw_data = json.load(f)

    cleaned_data = []
    for product in raw_data:
        cleaned_product = {
            "external_id": product.get("id"),
            "name": product.get("name"),
            "code": product.get("code"),
            "article": product.get("article"),
            "price": product.get("salePrices", [{}])[0].get("value", 0) / 100 if product.get("salePrices") else None,
            "min_price": product.get("minPrice", {}).get("value", 0) / 100 if product.get("minPrice") else None,
            "archived": product.get("archived", False),
            "updated_at": product.get("updated"),
            "category_id": product.get("productFolder", {}).get("meta", {}).get("href", "").split("/")[-1],
            "category_name": product.get("pathName", "").split("/")[-1] if product.get("pathName") else None,
            "pathName": product.get("pathName")  # Добавляем полный pathName
        }
        cleaned_data.append(cleaned_product)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

def convert_json_to_xml(json_file, xml_file):
    """
    Конвертирует JSON файл в XML.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    root = ET.Element("products")
    for product in data:
        product_elem = ET.SubElement(root, "product")
        for key, value in product.items():
            ET.SubElement(product_elem, key).text = str(value)

    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    with open(xml_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)

def process_data():
    """
    Основная функция для обработки данных.
    """
    input_file = settings.OUTPUT_FILE
    cleaned_json_file = input_file.replace('.json', '_cleaned.json')
    xml_file = cleaned_json_file.replace('.json', '.xml')

    process_and_clean_data(input_file, cleaned_json_file)
    convert_json_to_xml(cleaned_json_file, xml_file)

    return cleaned_json_file, xml_file
