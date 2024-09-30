  # app/routers/products.py
from fastapi import APIRouter, HTTPException
from app.utils.utils import logger
import json
import os

router = APIRouter()

@router.get("/products")
async def get_products():
    """
    GET запрос. Выводит полный список товаров из файла data/products_cleaned.json.
    """
    try:
        file_path = os.path.join('data', 'products_cleaned.json')
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")
        with open(file_path, 'r') as f:
            products = json.load(f)
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении списка продуктов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
