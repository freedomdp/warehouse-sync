from fastapi import APIRouter, HTTPException, Query
from app.utils.utils import logger
from app.config.field_mapping import FIELD_MAPPING
import json
import os
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import re

router = APIRouter()

# Соответствие названий полей
FIELD_CORRESPONDENCE = {
    "id": "external_id",
    "name": "name",
    "description": "description",
    "code": "code",
    "article": "article",
    "salePrices": "sale_price",
    "updated": "updated_at",
    "pathName": "pathName"
}

def create_xml(products, category):
    root = ET.Element("products")

    # Добавляем соответствие названий полей в начало XML
    correspondence = ET.SubElement(root, "field_correspondence")
    for source, target in FIELD_CORRESPONDENCE.items():
        field = ET.SubElement(correspondence, "field")
        ET.SubElement(field, "source").text = source
        ET.SubElement(field, "target").text = target

    for product in products:
        product_elem = ET.SubElement(root, "product")
        for source_key, target_key in FIELD_CORRESPONDENCE.items():
            value = product.get(target_key, "")
            field_elem = ET.SubElement(product_elem, target_key)
            field_elem.text = str(value)

    tree = ET.ElementTree(root)

    # Создаем безопасное имя файла
    safe_filename = re.sub(r'[^\w\-_\. ]', '_', category)
    xml_filename = f"data/{safe_filename}.xml"

    # Записываем XML с отступами для лучшей читаемости
    ET.indent(tree, space="  ", level=0)
    tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
    return xml_filename

@router.get("/simple_category")
async def get_products_by_category(category: str = Query(..., description="Category name")):
    try:
        file_path = os.path.join('data', 'products_cleaned.json')
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Декодируем категорию из URL-encoded формата
        decoded_category = unquote(category)

        category_products = [p for p in products if p.get('pathName') and decoded_category in p['pathName']]

        if not category_products:
            raise HTTPException(status_code=404, detail="Category not found or contains no products")

        # Создаем XML файл
        xml_filename = create_xml(category_products, decoded_category)

        return {
            "category": decoded_category,
            "products_count": len(category_products),
            "products": category_products,
            "xml_file": xml_filename
        }
    except Exception as e:
        logger.error(f"Ошибка при получении товаров категории: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
