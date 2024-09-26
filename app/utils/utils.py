import time
import pytz
import logging
import sys
import os
import psutil
import gc
import asyncio
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings
from app.config.field_mapping import FIELD_MAPPING

kiev_tz = pytz.timezone('Europe/Kiev')
Base = declarative_base()

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(os.path.join(log_dir, 'sync.log'))
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

logger = setup_logger('app')

def create_async_db_engine(database_url):
    return create_async_engine(database_url.replace('mysql://', 'mysql+aiomysql://'), echo=True)

def create_async_session_factory(engine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session

async def wait_for_db(engine, max_retries=60, retry_interval=5):
    for _ in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            logger.info("База данных готова")
            return
        except Exception as e:
            logger.warning(f"Ожидание базы данных... ({e})")
            await asyncio.sleep(retry_interval)
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

def json_to_xml(json_file_path, xml_file_path):
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    root = ET.Element('products')
    for item in data:
        product = ET.SubElement(root, 'product')
        for key, value in FIELD_MAPPING.items():
            if key in item:
                ET.SubElement(product, value).text = str(item[key])

    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    with open(xml_file_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_str)

    logger.info(f"XML file has been created at {xml_file_path}")

# Создание асинхронного движка и фабрики сессий
async_engine = create_async_db_engine(settings.DATABASE_URL)
AsyncSessionLocal = create_async_session_factory(async_engine)
