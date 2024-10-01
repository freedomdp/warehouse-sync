import os
import logging
from fastapi import APIRouter, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from datetime import datetime
import pytz
from app.config.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Настройки для таблицы
HEADER_ROW_HEIGHT = 32
DATA_ROW_HEIGHT = 200
COLUMN_ORDER = ['Article', 'Code', 'Path Name', 'Name', 'Description', 'Sale Price', 'Stock']
COLUMN_WIDTHS = [85, 85, 100, 150, 450, 75, 75]

def get_google_sheets_service():
    logger.info("Попытка получения сервиса Google Sheets")
    if not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        logger.error(f"Файл с учетными данными Google не найден: {settings.GOOGLE_CREDENTIALS_FILE}")
        raise FileNotFoundError(f"Файл с учетными данными Google не найден: {settings.GOOGLE_CREDENTIALS_FILE}")

    try:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)
        logger.info("Сервис Google Sheets успешно получен")
        return service
    except Exception as e:
        logger.error(f"Ошибка при получении сервиса Google Sheets: {str(e)}")
        raise

@router.get("/warehouse_stock_to_googlesheets")
async def warehouse_stock_to_googlesheets():
    try:
        logger.info("Начало обработки запроса /warehouse_stock_to_googlesheets")

        # Чтение данных из JSON файла
        logger.info("Чтение данных из warehouse_stock_result.json")
        with open('data/warehouse_stock_result.json', 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        logger.info(f"Прочитано {len(stock_data)} записей из warehouse_stock_result.json")

        # Чтение данных о товарах из products_cleaned.json
        logger.info("Чтение данных из products_cleaned.json")
        with open('data/products_cleaned.json', 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        logger.info(f"Прочитано {len(products_data)} записей из products_cleaned.json")

        # Создание словаря для быстрого поиска pathName по артикулу
        products_dict = {item['article']: item.get('pathName', '') for item in products_data if 'article' in item}
        logger.info(f"Создан словарь products_dict с {len(products_dict)} записями")

        # Подготовка данных для записи
        rows = [COLUMN_ORDER]  # Заголовок
        for item in stock_data:
            if 'article' not in item:
                logger.warning(f"Пропущена запись без артикула: {item}")
                continue
            if 'code' not in item:
                logger.warning(f"Пропущена запись без кода: {item}")
                continue

            row = [
                item.get('article', ''),
                item.get('code', ''),
                products_dict.get(item.get('article', ''), ''),  # Path Name из products_cleaned.json
                item.get('name', ''),
                item.get('description', ''),
                item.get('sale_price', ''),
                item.get('stock', '')
            ]
            rows.append(row)

        logger.info(f"Подготовлено {len(rows) - 1} строк для записи в Google Sheets")

        # Создание нового листа
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        kiev_tz = pytz.timezone('Europe/Kiev')
        sheet_name = datetime.now(kiev_tz).strftime("%d.%m.%Y %H:%M")
        logger.info(f"Создание нового листа с именем {sheet_name}")
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
        }
        response = sheet.batchUpdate(spreadsheetId=settings.GOOGLE_SPREADSHEET_ID, body=request_body).execute()
        new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        logger.info(f"Создан новый лист с ID {new_sheet_id}")

        # Запись данных в новый лист
        logger.info("Запись данных в новый лист")
        range_name = f"{sheet_name}!A1"
        body = {'values': rows}
        sheet.values().update(
            spreadsheetId=settings.GOOGLE_SPREADSHEET_ID, range=range_name,
            valueInputOption='RAW', body=body).execute()

        # Форматирование таблицы
        logger.info("Форматирование таблицы")
        requests = [
            # Установка высоты заголовка
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': 0,
                        'endIndex': 1
                    },
                    'properties': {
                        'pixelSize': HEADER_ROW_HEIGHT
                    },
                    'fields': 'pixelSize'
                }
            },
            # Установка высоты остальных строк
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': 1,
                        'endIndex': len(rows)
                    },
                    'properties': {
                        'pixelSize': DATA_ROW_HEIGHT
                    },
                    'fields': 'pixelSize'
                }
            },
            # Жирный шрифт для заголовка
            {
                'repeatCell': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold'
                }
            },
            # Закрепление первой строки
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': new_sheet_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            },
            # Установка переноса текста и вертикального выравнивания для всех ячеек
            {
                'repeatCell': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': len(rows)
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'wrapStrategy': 'WRAP',
                            'verticalAlignment': 'MIDDLE'
                        }
                    },
                    'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'
                }
            }
        ]

        # Установка ширины колонок
        for i, width in enumerate(COLUMN_WIDTHS):
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': i,
                        'endIndex': i + 1
                    },
                    'properties': {
                        'pixelSize': width
                    },
                    'fields': 'pixelSize'
                }
            })

        sheet.batchUpdate(spreadsheetId=settings.GOOGLE_SPREADSHEET_ID, body={'requests': requests}).execute()
        logger.info("Форматирование таблицы завершено")

        logger.info("Обработка запроса /warehouse_stock_to_googlesheets завершена успешно")
        return {
            "message": f"Данные успешно выгружены в Google Sheets. Создан новый лист: {sheet_name}",
            "processed_items": len(rows) - 1  # Исключаем строку заголовка
        }

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
