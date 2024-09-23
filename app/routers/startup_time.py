from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.startup_time import StartupTime

router = APIRouter()

@router.get("/startup-time")
async def get_startup_time(db: Session = Depends(get_db)):
    startup_time = db.query(StartupTime).order_by(StartupTime.id.desc()).first()
    if startup_time:
        return {"startup_time": startup_time.id.strftime("%d.%m.%Y %H:%M:%S")}
    return {"error": "Время запуска не найдено"}
