from fastapi import APIRouter, HTTPException
from app.services.async_sync_service import AsyncSyncService
from app.utils.utils import logger
from app.config.field_mapping import map_product
import json
import os

router = APIRouter()

@router.get("/sync-2")
async def sync_products_async():
    """
    GET запрос. Запускает асинхронную синхронизацию продуктов с "Мой склад"
    и создает очищенный файл данных.
    """
    try:
        async_sync_service = AsyncSyncService()
        products = await async_sync_service.run_async_sync()

        # Создаем очищенный файл данных
        cleaned_products = [map_product(product) for product in products]

        output_file = os.path.join('data', 'products_cleaned.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_products, f, ensure_ascii=False, indent=2)

        return {
            "message": "Асинхронная синхронизация завершена успешно",
            "products_count": len(cleaned_products),
            "cleaned_file": output_file
        }
    except Exception as e:
        logger.error(f"Ошибка при асинхронной синхронизации продуктов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
