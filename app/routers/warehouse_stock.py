from fastapi import APIRouter, HTTPException
from app.services.warehouse_stock_service import warehouse_stock_service
from app.utils.utils import logger

router = APIRouter()

@router.get("/warehouse_stock")
async def get_warehouse_stock():
    """
    GET запрос. Получает все данные о складских запасах с МойСклад в асинхронном режиме.
    """
    logger.info("Начало обработки запроса GET /warehouse_stock")
    try:
        result = await warehouse_stock_service.get_warehouse_stock()
        logger.info("Запрос GET /warehouse_stock успешно обработан")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении данных о складских запасах: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
