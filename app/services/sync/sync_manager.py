# Файл для управления процессом синхронизации

from datetime import datetime
import json
from app.services.sync.auth_service import AuthService
from app.services.sync.data_retrieval_service import DataRetrievalService
from app.utils.utils import logger
from app.config import settings

class SyncManager:
    def __init__(self):
        self.auth_service = AuthService()
        self.data_retrieval_service = DataRetrievalService()
        self.last_sync_time = None

    async def run_sync(self):
        logger.info("Начало процесса синхронизации")
        try:
            if not await self.auth_service.test_auth():
                logger.error("Ошибка аутентификации")
                raise Exception("Ошибка аутентификации")
            logger.info("Аутентификация успешна")

            total_products = await self.data_retrieval_service.fetch_all_products()
            self.last_sync_time = datetime.now().isoformat()

            logger.info(f"Процесс синхронизации завершен. Получено {total_products} товаров.")
            return self.get_products_from_file()
        except Exception as e:
            logger.error(f"Ошибка при выполнении синхронизации: {str(e)}")
            raise

    def get_products_from_file(self):
        try:
            with open(self.data_retrieval_service.output_file, 'r') as f:
                products = json.load(f)
            logger.info(f"Прочитано {len(products)} товаров из файла")
            return products
        except Exception as e:
            logger.error(f"Ошибка при чтении файла с продуктами: {str(e)}")
            return []
