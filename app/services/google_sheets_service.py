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
            sheet = self.service.spreadsheets()

            # Очищаем существующий лист
            sheet.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:Z"
            ).execute()

            # Подготавливаем данные для вставки
            headers = list(data[0].keys())
            values = [headers]
            for item in data:
                values.append([str(item.get(key, '')) for key in headers])

            # Разбиваем данные на части по 5000 строк
            batch_size = 5000
            for i in range(0, len(values), batch_size):
                batch = values[i:i+batch_size]

                body = {'values': batch}
                for attempt in range(3):  # Попытки повтора при ошибке
                    try:
                        sheet.values().append(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{self.sheet_name}!A1",
                            valueInputOption='RAW',
                            body=body
                        ).execute()
                        break
                    except HttpError as e:
                        if e.resp.status in [403, 500, 503]:  # Ошибки, которые могут быть временными
                            logger.warning(f"Attempt {attempt + 1} failed. Retrying...")
                            time.sleep(5)  # Пауза перед повторной попыткой
                        else:
                            raise

            # Добавляем комментарий с датой выгрузки
            kiev_tz = pytz.timezone('Europe/Kiev')
            current_time = datetime.now(kiev_tz).strftime("%d.%m.%Y %H:%M")
            comment = f'Дата выгрузки: {current_time}'

            sheet.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    "requests": [
                        {
                            "updateCells": {
                                "range": {
                                    "sheetId": 0,
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
