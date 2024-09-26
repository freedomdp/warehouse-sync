from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Строка подключения к базе данных
    DATABASE_URL: str
    # Логин для доступа к API МойСклад
    MY_SKLAD_LOGIN: str
    # Пароль для доступа к API МойСклад
    MY_SKLAD_PASSWORD: str
    # URL API МойСклад
    MY_SKLAD_API_URL: str
    # Пароль root пользователя MySQL
    MYSQL_ROOT_PASSWORD: str
    # Имя базы данных MySQL
    MYSQL_DATABASE: str
    # Имя пользователя MySQL
    MYSQL_USER: str
    # Пароль пользователя MySQL
    MYSQL_PASSWORD: str
    # Количество товаров, получаемое за один сеанс при обращении по API
    BATCH_SIZE: int = 100
    # Общее количество получаемых товаров (0 - все товары на сервере)
    TOTAL_PRODUCTS: int = 500
    # Путь и название файла для сохранения данных о товарах
    OUTPUT_FILE: str = '/app/data/products.json'
    # Порог использования памяти (в процентах)
    MEMORY_THRESHOLD: int = 90
    # Задержка между запросами в секундах
    REQUEST_DELAY: float = 2.0

    class Config:
        env_file = ".env"

settings = Settings()
