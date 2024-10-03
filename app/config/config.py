from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # URL API МойСклад
    MY_SKLAD_API_URL: str
    # Логин для доступа к API МойСклад
    MY_SKLAD_LOGIN: str
    # Пароль для доступа к API МойСклад
    MY_SKLAD_PASSWORD: str
    # Количество товаров, получаемое за один сеанс при обращении по API
    BATCH_SIZE: int = 1000
    # Общее количество получаемых товаров (0 - все товары на сервере)
    TOTAL_PRODUCTS: int = 0
    # Задержка между запросами в секундах
    REQUEST_DELAY: float = 2.0
    # Корневая директория для данных
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    # Директория для архивов
    ARCHIVE_DIR: str = os.path.join(DATA_DIR, 'arc')
    # Директория для JSON файлов
    JSON_DIR: str = os.path.join(DATA_DIR, 'json')
    # Директория для XML файлов
    XML_DIR: str = os.path.join(DATA_DIR, 'xml')
    # Путь и название файла для сохранения данных о товарах
    OUTPUT_FILE: str = os.path.join(DATA_DIR, 'products.json')
    # ID Google таблицы
    GOOGLE_SPREADSHEET_ID: str = '1kwopnPKCGNeVL-NMjvHE0y6PBugoxJoZgDcwBRb0BN0'
    # Имя листа в Google таблице
    GOOGLE_SHEET_NAME: str = 'Data'
    # Путь к файлу с учетными данными Google
    GOOGLE_CREDENTIALS_FILE: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials', 'google_sheets_credentials.json')

    class Config:
        env_file = ".env"

settings = Settings()

# Создаем необходимые директории
os.makedirs(settings.ARCHIVE_DIR, exist_ok=True)
os.makedirs(settings.JSON_DIR, exist_ok=True)
os.makedirs(settings.XML_DIR, exist_ok=True)
