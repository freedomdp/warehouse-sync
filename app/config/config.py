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
    # Путь и название файла для сохранения данных о товарах
    OUTPUT_FILE: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'products.json')

    class Config:
        env_file = ".env"

settings = Settings()
