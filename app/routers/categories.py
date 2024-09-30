from fastapi import APIRouter, HTTPException
from app.utils.utils import logger
from app.config import settings
import json
import os

router = APIRouter()

@router.get("/categories")
async def get_categories():
    try:
        file_path = os.path.join('data', 'products_cleaned.json')
        if not os.path.exists(file_path):
            return {"simple_list": [], "structured_list": {}}

        with open(file_path, 'r') as f:
            products = json.load(f)

        if not products:
            return {"simple_list": [], "structured_list": {}}

        categories = set(product.get('pathName') for product in products if product.get('pathName'))

        structured_categories = {}
        for path in categories:
            parts = path.split('/')
            current = structured_categories
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        return {
            "simple_list": sorted(list(categories)),
            "structured_list": structured_categories
        }
    except Exception as e:
        logger.error(f"Ошибка при получении списка категорий: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
