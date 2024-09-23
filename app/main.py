import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base, SessionLocal
from app.routers import startup_time, product
from app.models import StartupTime
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        kiev_tz = pytz.timezone('Europe/Kiev')
        current_time = datetime.now(kiev_tz)
        startup_time = StartupTime(id=current_time)
        db.add(startup_time)
        db.commit()
        logger.info(f"Сервер запущен в {current_time}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении времени запуска: {e}")
    finally:
        db.close()

# Подключаем роутеры
app.include_router(startup_time.router)
app.include_router(product.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
