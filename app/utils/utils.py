import time
import pytz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings


kiev_tz = pytz.timezone('Europe/Kiev')

Base = declarative_base()

def create_db_engine(database_url):
    return create_engine(database_url)

def create_session_local(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_db(engine, max_retries=60, retry_interval=5):
    for _ in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("База данных готова")
            return
        except Exception as e:
            print(f"Ожидание базы данных... ({e})")
            time.sleep(retry_interval)
    raise Exception("Не удалось подключиться к базе данных")

# Создание engine и SessionLocal здесь, чтобы их можно было импортировать
engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = create_session_local(engine)
