from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings
from app.utils.utils import logger
import time

class GoogleSheetsService:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)

    async def upload_to_sheets(self, data):
        """
        Выгружает данные в Google Sheets с поддержкой больших объемов данных.
        """
        try:
            sheet = self.service.spreadsheets()

            # Создаем новый лист
            spreadsheet = sheet.create(body={
                'properties': {'title': 'Product Data'}
            }).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

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
                            spreadsheetId=spreadsheet_id,
                            range='Sheet1',
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

            logger.info(f"Данные успешно выгружены в Google Sheets. Всего строк: {len(values)}")

            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        except Exception as e:
            logger.error(f"Ошибка при выгрузке в Google Sheets: {str(e)}", exc_info=True)
            raise

google_sheets_service = GoogleSheetsService()
