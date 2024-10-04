from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings
from app.utils.utils import logger
import time
from datetime import datetime
import pytz

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

            # Определяем порядок столбцов
            columns = ['id', 'article', 'code', 'externalCode', 'pathname', 'name', 'description', 'salePrice', 'store', 'stock', 'updated']

            # Подготавливаем данные для вставки
            values = [columns]  # Заголовки
            for item in data:
                row = [str(item.get(col, '')) for col in columns]
                values.append(row)

            # Вставляем данные
            sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': values}
            ).execute()

            # Форматирование: закрепление первой строки и жирный шрифт
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

            sheets.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()

            # Добавляем комментарий с датой выгрузки
            kiev_tz = pytz.timezone('Europe/Kiev')
            current_time = datetime.now(kiev_tz).strftime("%d.%m.%Y %H:%M")
            comment = f'Дата выгрузки: {current_time}'
            sheets.batchUpdate(
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

            logger.info(f"Данные успешно выгружены в Google Sheets. Всего строк: {len(values)}")
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        except Exception as e:
            logger.error(f"Ошибка при выгрузке в Google Sheets: {str(e)}", exc_info=True)
            raise

google_sheets_service = GoogleSheetsService()
