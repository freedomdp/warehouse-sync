# app/routers/root.py
from fastapi import APIRouter
from datetime import datetime
import pytz

router = APIRouter()

@router.get("/")
async def root():
    """
    GET запрос. Показывает статус сервера, дату и время его запуска (временная зона +3).
    """
    tz = pytz.timezone('Europe/Kyiv')
    start_time = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")
    return {
        "status": "Server is running",
        "start_time": start_time
    }
