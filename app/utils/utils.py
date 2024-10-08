import pytz
import logging
import sys
import os
import psutil
import gc
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from app.config import settings
from app.config.field_mapping import FIELD_MAPPING


kiev_tz = pytz.timezone('Europe/Kiev')

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

def json_to_xml(data, xml_file_path):
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

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
        return {}
