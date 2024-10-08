from pydantic_settings import BaseSettings

class WooConfig(BaseSettings):
    WOO_URL: str = "https://vtoman.com.ua"
    WOO_CONSUMER_KEY: str = "ck_62e2827ea15b125f4f4015f517c317d73f1177fe"
    WOO_CONSUMER_SECRET: str = "cs_bca58219376e01dcbd54e0cf8a89da79a908d3db"
    WOO_VERSION: str = "wc/v3"
    XML_FOLDER_URL: str = "https://vtoman.com.ua/XML/"
    JSON_FILE_PATH: str = "data/json/combined_products.json"

woo_config = WooConfig()
