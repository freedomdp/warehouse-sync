import time
import pytz
import logging
import sys
import os
import psutil
import gc
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config.config import settings

kiev_tz = pytz.timezone('Europe/Kiev')
Base = declarative_base()

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('logs/sync.log')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

logger = setup_logger(__name__)

def create_db_engine(database_url):
    return create_engine(database_url)

def create_session_local(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_db(engine, max_retries=60, retry_interval=5):
    for _ in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("База данных готова")
            return
        except Exception as e:
            logger.warning(f"Ожидание базы данных... ({e})")
            time.sleep(retry_interval)
    raise Exception("Не удалось подключиться к базе данных")

def check_memory_usage(threshold):
    memory = psutil.virtual_memory()
    return memory.percent > threshold

def check_file_growth(file_path, previous_size):
    current_size = os.path.getsize(file_path)
    return current_size > previous_size

def adjust_batch_size(current_batch_size):
    new_batch_size = max(2, current_batch_size // 2)
    if new_batch_size != current_batch_size:
        logger.warning(f"Уменьшаем размер партии с {current_batch_size} до {new_batch_size}")
    return new_batch_size

async def handle_memory_overflow(file_path, current_batch_size):
    previous_size = os.path.getsize(file_path)
    if check_file_growth(file_path, previous_size):
        logger.info("Размер файла увеличился, продолжаем работу")
        return current_batch_size
    else:
        logger.warning("Размер файла не увеличился после получения данных")
        return adjust_batch_size(current_batch_size)

def clear_memory():
    gc.collect()
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f"Memory usage after cleanup: {memory_info.rss / 1024 / 1024:.2f} MB")

# Создание engine и SessionLocal здесь, чтобы их можно было импортировать
engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = create_session_local(engine)
