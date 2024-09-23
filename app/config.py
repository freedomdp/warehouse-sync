from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MY_SKLAD_LOGIN: str
    MY_SKLAD_PASSWORD: str
    MY_SKLAD_API_URL: str
    MYSQL_ROOT_PASSWORD: str
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    class Config:
        env_file = ".env"

settings = Settings()
