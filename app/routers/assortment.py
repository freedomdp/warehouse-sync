from fastapi import APIRouter, HTTPException
from app.services.assortment_service import assortment_service
from app.utils.utils import logger

router = APIRouter()

@router.get("/assortment")
async def get_assortment():
    """
    GET запрос. Получает данные об ассортименте товаров с МойСклад в асинхронном режиме.
    """
    logger.info("Начало обработки запроса GET /assortment")
    try:
        result = await assortment_service.get_assortment()
        logger.info("Запрос GET /assortment успешно обработан")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении данных об ассортименте: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
