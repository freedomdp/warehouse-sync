from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_session
from app.models.startup_time import StartupTime

router = APIRouter()

@router.get("/startup-time")
async def get_startup_time(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(StartupTime).order_by(StartupTime.id.desc())
    )
    startup_time = result.scalar_one_or_none()
    if startup_time:
        return {"startup_time": startup_time.id.strftime("%d.%m.%Y %H:%M:%S")}
    return {"error": "Время запуска не найдено"}
