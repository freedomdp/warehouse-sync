from fastapi import APIRouter, HTTPException, Query
from app.services.warehouse_stock_service import warehouse_stock_service
from app.utils.utils import logger
from typing import Optional

router = APIRouter()

@router.get("/warehouse_stock")
async def get_warehouse_stock(
    filter: Optional[str] = Query(None, description="Параметры фильтрации в формате key1=value1&key2=value2")
):
    """
    GET запрос. Получает данные о складских запасах с МойСклад в асинхронном режиме.
    """
    logger.info("Начало обработки запроса GET /warehouse_stock")
    try:
        filter_params = {}
        if filter:
            filter_params = dict(param.split('=') for param in filter.split('&'))

        result = await warehouse_stock_service.get_warehouse_stock(filter_params)
        logger.info("Запрос GET /warehouse_stock успешно обработан")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении данных о складских запасах: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
