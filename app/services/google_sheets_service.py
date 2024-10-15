from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings
from app.utils.utils import logger
import time
import random
import pytz
from datetime import datetime

class GoogleSheetsService:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.spreadsheet_id = settings.GOOGLE_SPREADSHEET_ID
        self.sheet_name = settings.GOOGLE_SHEET_NAME

    async def upload_to_sheets(self, data):
        """
        Выгружает данные в существующую Google таблицу с поддержкой больших объемов данных.
        """
        try:
            sheets = self.service.spreadsheets()

            # Получаем ID листа
            sheet_metadata = sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']

            # Очищаем существующий лист
            sheets.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:Z"
            ).execute()

            # Определяем порядок столбцов, добавляем image_links
            columns = ['id', 'article', 'code', 'externalCode', 'pathname', 'name', 'description', 'salePrice', 'store', 'stock', 'updated', 'image_links']

            # Подготавливаем данные для вставки
            values = [columns]  # Заголовки
            for item in data:
                row = [str(item.get(col, '')) for col in columns[:-1]]  # Все столбцы кроме image_links
                # Обрабатываем image_links отдельно
                image_links = item.get('image_links', [])
                row.append('\n'.join(image_links) if image_links else '')
                values.append(row)

            logger.info(f"Подготовлено {len(values) - 1} строк для загрузки в Google Sheets")

            # Разбиваем данные на части и вставляем
            batch_size = 1000
            total_uploaded = 0
            for i in range(0, len(values), batch_size):
                batch = values[i:i+batch_size]
                body = {'values': batch}
                for attempt in range(5):  # Попытки повтора при ошибке
                    try:
                        response = sheets.values().append(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{self.sheet_name}!A1",
                            valueInputOption='RAW',
                            body=body
                        ).execute(num_retries=3)
                        total_uploaded += len(batch) - 1  # Вычитаем 1, так как первая строка - заголовки
                        logger.info(f"Загружено {len(batch)} строк. Всего: {total_uploaded}")
                        break
                    except HttpError as e:
                        if e.resp.status in [403, 500, 503] and attempt < 4:
                            wait_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            raise

            # Проверяем количество загруженных строк
            result = sheets.values().get(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!A:A").execute()
            actual_rows = len(result.get('values', [])) - 1  # Вычитаем 1, так как первая строка - заголовки
            if actual_rows != len(data):
                logger.error(f"Несоответствие количества строк: загружено {actual_rows}, ожидалось {len(data)}")
                raise Exception("Количество загруженных строк не соответствует ожидаемому")

            # Применяем форматирование
            self.apply_formatting(sheet_id)

            # Добавляем комментарий с датой выгрузки
            self.add_upload_date_comment(sheet_id)

            logger.info(f"Данные успешно выгружены в Google Sheets. Всего строк: {actual_rows}")
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        except Exception as e:
            logger.error(f"Ошибка при выгрузке в Google Sheets: {str(e)}", exc_info=True)
            raise

    def apply_formatting(self, sheet_id):
        """Применяет форматирование к таблице."""
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            }
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": requests}
        ).execute()

    def add_upload_date_comment(self, sheet_id):
        """Добавляет комментарий с датой выгрузки."""
        kiev_tz = pytz.timezone('Europe/Kiev')
        current_time = datetime.now(kiev_tz).strftime("%d.%m.%Y %H:%M")
        comment = f'Дата выгрузки: {current_time}'

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={
                "requests": [
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "note": comment
                                        }
                                    ]
                                }
                            ],
                            "fields": "note"
                        }
                    }
                ]
            }
        ).execute()

google_sheets_service = GoogleSheetsService()
