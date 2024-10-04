from fastapi import APIRouter, HTTPException
from app.services.product_collector_service import product_collector_service
from app.utils.utils import logger

router = APIRouter()

@router.get("/collect_products")
async def collect_products():
    """
    GET запрос. Собирает данные о товарах из всех источников, обрабатывает их и сохраняет в
    различных форматах.
    """
    logger.info("Начало обработки запроса GET /collect_products")
    try:
        result = await product_collector_service.collect_and_process_data()
        logger.info("Запрос GET /collect_products успешно обработан")
        return result
    except Exception as e:
        logger.error(f"Ошибка при сборе данных о товарах: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
