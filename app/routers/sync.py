from fastapi import APIRouter, HTTPException
from app.services.sync.sync_manager import SyncManager
from app.utils.utils import logger
from app.config.field_mapping import map_product
import json
import os

router = APIRouter()

@router.get("/sync")
async def sync_products():
    """
    GET запрос. Запускает синхронизацию продуктов с "Мой склад"
    и создает очищенный файл данных.
    """
    try:
        sync_manager = SyncManager()
        result = await sync_manager.run_sync()

        # Создаем очищенный файл данных
        cleaned_products = [map_product(product) for product in result]

        output_file = os.path.join('data', 'products_cleaned.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_products, f, ensure_ascii=False, indent=2)

        return {
            "message": "Синхронизация завершена успешно",
            "products_count": len(cleaned_products),
            "cleaned_file": output_file
        }
    except Exception as e:
        logger.error(f"Ошибка при синхронизации продуктов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
