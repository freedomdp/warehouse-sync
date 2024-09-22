import time
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import pytz

app = FastAPI()

# Настройка базы данных
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение часового пояса Киева
kiev_tz = pytz.timezone('Europe/Kiev')

# Модель для времени запуска
class StartupTime(Base):
    __tablename__ = "startup_time"
    id = Column(DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(kiev_tz))

def wait_for_db(max_retries=30, retry_interval=2):
    """Ожидание готовности базы данных"""
    for _ in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            print("База данных готова")
            return
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            time.sleep(retry_interval)
    raise Exception("Не удалось подключиться к базе данных")

@app.on_event("startup")
async def startup_event():
    """Функция, выполняемая при запуске приложения"""
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(StartupTime).delete()
    db.add(StartupTime())
    db.commit()
    db.close()
    print("Время запуска записано в базу данных")

@app.get("/startup-time")
async def get_startup_time():
    """Возвращает время запуска сервера"""
    db = SessionLocal()
    startup_time = db.query(StartupTime).first()
    db.close()
    if startup_time:
        kiev_time = startup_time.id.astimezone(kiev_tz)
        return {"startup_time": kiev_time.strftime("%d.%m.%Y %H:%M:%S")}
    return {"error": "Время запуска не найдено"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
