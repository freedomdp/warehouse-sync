import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException
from app.services.sync.auth_service import AuthService
from app.utils.utils import logger
from app.config import settings
import os
from multiprocessing import Pool

router = APIRouter()

async def get_warehouse_stock(session, headers):
    """
    Асинхронно получает расширенные данные об остатках товаров.
    """
    url = f"{settings.MY_SKLAD_API_URL}/report/stock/all"
    params = {
        "limit": 1000,
        "offset": 0,
        "groupBy": "product"
    }
    stock_data = []

    try:
        while True:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                stock_data.extend(data.get("rows", []))

                # Проверяем, есть ли следующая страница
                next_href = data.get("meta", {}).get("nextHref")
                if not next_href:
                    break

                # Обновляем offset для следующего запроса
                params["offset"] += params["limit"]

        return stock_data
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка при получении данных об остатках: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных об остатках")

def save_raw_data(data, filename="data/warehouse_stock_raw.json"):
    """
    Сохраняет "сырые" данные в JSON файл.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Сырые данные сохранены в {filename}")
    except IOError as e:
        logger.error(f"Ошибка при сохранении сырых данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении сырых данных")

def load_products_data(filename="data/products_cleaned.json"):
    """
    Загружает данные о товарах из JSON файла.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        logger.error(f"Ошибка при загрузке данных о товарах: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке данных о товарах")

def process_item(item, products_dict):
    """
    Обрабатывает отдельный товар для параллельной обработки.
    """
    article = item.get('article')
    if article in products_dict:
        product_info = products_dict[article]
        return {
            "article": article,
            "name": product_info.get("name"),
            "description": product_info.get("description"),
            "sale_price": product_info.get("sale_price"),
            "code": product_info.get("code"),
            "stock": item.get("stock"),
            "pathName": product_info.get("pathName")
        }
    return None

def combine_data(stock_data, products_data):
    """
    Совмещает данные об остатках с информацией о товарах.
    """
    products_dict = {}
    for product in products_data:
        if 'article' in product:
            products_dict[product['article']] = product
        else:
            logger.warning(f"Товар без артикула в products_cleaned.json: {product.get('name', 'Неизвестный товар')}")

    combined_data = []
    skipped_items = 0

    for item in stock_data:
        article = item.get('article')
        if not article:
            logger.warning(f"Пропущен товар без артикула в данных о запасах: {item.get('name', 'Неизвестный товар')}")
            skipped_items += 1
            continue

        if article in products_dict:
            product_info = products_dict[article]
            sale_price = item.get("salePrice") or product_info.get("sale_price")
            if sale_price is not None:
                sale_price = float(sale_price) / 100  # Корректировка цены

            combined_data.append({
                "article": article,
                "name": item.get("name") or product_info.get("name"),
                "description": product_info.get("description"),
                "sale_price": sale_price,
                "code": item.get("code") or product_info.get("code"),
                "stock": item.get("stock"),
                "pathName": product_info.get("pathName")
            })
        else:
            logger.warning(f"Артикул {article} не найден в products_cleaned.json")
            skipped_items += 1

    logger.info(f"Обработано товаров: {len(combined_data)}, Пропущено товаров: {skipped_items}")
    return combined_data

def save_json_result(data, filename="data/warehouse_stock_result.json"):
    """
    Сохраняет результат в JSON файл.
    """
    try:
        # Корректировка цен перед сохранением
        for item in data:
            if 'sale_price' in item and item['sale_price'] is not None:
                item['sale_price'] = float(item['sale_price'])

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Результат сохранен в JSON: {filename}")
    except IOError as e:
        logger.error(f"Ошибка при сохранении результата в JSON: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении результата в JSON")

def save_xml_result(data, filename="data/warehouse_stock_result.xml"):
    """
    Сохраняет результат в XML файл.
    """
    try:
        root = ET.Element("warehouse_stock")
        for item in data:
            product = ET.SubElement(root, "product")
            for key, value in item.items():
                if key == 'sale_price' and value is not None:
                    value = float(value)
                ET.SubElement(product, key).text = str(value)

        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        logger.info(f"Результат сохранен в XML: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении результата в XML: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении результата в XML")

@router.get("/warehouse_stock")
async def warehouse_stock():
    """
    Эндпоинт для получения и обработки данных об остатках на складе.
    """
    try:
        auth_service = AuthService()
        headers = auth_service.get_auth_header()

        async with aiohttp.ClientSession() as session:
            stock_data = await get_warehouse_stock(session, headers)

        logger.info(f"Получено {len(stock_data)} записей об остатках")
        save_raw_data(stock_data)

        products_data = load_products_data()
        logger.info(f"Загружено {len(products_data)} товаров из products_cleaned.json")

        combined_data = combine_data(stock_data, products_data)

        save_json_result(combined_data)
        save_xml_result(combined_data)

        return {
            "message": "Данные об остатках успешно обработаны и сохранены",
            "processed_items": len(combined_data),
            "total_stock_items": len(stock_data),
            "total_products": len(products_data)
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
