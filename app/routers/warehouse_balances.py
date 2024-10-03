from fastapi import APIRouter, HTTPException
from app.services.warehouse_balances_service import warehouse_balances_service
from app.utils.utils import logger

router = APIRouter()

@router.get("/warehouse_balances")
async def get_warehouse_balances():
    """
    GET запрос. Получает данные об остатках по складам с МойСклад в асинхронном режиме.
    """
    logger.info("Начало обработки запроса GET /warehouse_balances")
    try:
        result = await warehouse_balances_service.get_warehouse_balances()
        logger.info("Запрос GET /warehouse_balances успешно обработан")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении данных об остатках по складам: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
