from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MY_SKLAD_LOGIN: str
    MY_SKLAD_PASSWORD: str
    MY_SKLAD_API_URL: str
    WORDPRESS_URL: str
    WORDPRESS_USERNAME: str
    WORDPRESS_PASSWORD: str

    class Config:
        env_file = ".env"

settings = Settings()

DATABASE_URL = settings.DATABASE_URL
