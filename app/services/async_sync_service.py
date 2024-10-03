import aiohttp
import gzip
import json
import os
from app.config import settings
from app.utils.utils import logger

class AsyncSyncService:
    """
    Класс для асинхронной синхронизации данных с МойСклад API.
    """

    def __init__(self):
        """
        Инициализация сервиса с настройками API.
        """
        self.base_url = settings.MY_SKLAD_API_URL
        self.headers = {
            "Authorization": f"Bearer {settings.MY_SKLAD_TOKEN}",
            "Accept-Encoding": "gzip"
        }

    async def create_async_task(self, endpoint):
        """
        Создает асинхронную задачу для получения данных.

        :param endpoint: Конечная точка API
        :return: Tuple с URL статуса и результата задачи
        """
        logger.info(f"Начало создания асинхронной задачи для эндпоинта: {endpoint}")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}?async=true"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 202:
                        logger.info(f"Асинхронная задача успешно создана для эндпоинта: {endpoint}")
                        return response.headers.get('Location'), response.headers.get('Content-Location')
                    else:
                        content = await response.text()
                        logger.error(f"Не удалось создать асинхронную задачу. Статус: {response.status}, Содержание: {content}")
                        return None, None
        except Exception as e:
            logger.error(f"Ошибка при создании асинхронной задачи: {str(e)}")
            raise

    async def check_task_status(self, status_url):
        """
        Проверяет статус асинхронной задачи.

        :param status_url: URL для проверки статуса
        :return: Словарь с информацией о статусе задачи
        """
        logger.info(f"Проверка статуса задачи: {status_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(status_url, headers=self.headers) as response:
                    if response.status == 200:
                        status = await response.json()
                        logger.info(f"Получен статус задачи: {status['status']}")
                        return status
                    else:
                        logger.error(f"Не удалось проверить статус задачи. Код ответа: {response.status}")
                        raise Exception(f"Не удалось проверить статус задачи: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса задачи: {str(e)}")
            raise

    async def get_task_result(self, result_url):
        """
        Получает результат выполнения асинхронной задачи.

        :param result_url: URL для получения результата
        :return: Декодированные данные результата
        """
        logger.info(f"Получение результата задачи: {result_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(result_url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        decompressed = gzip.decompress(content)
                        logger.info("Результат задачи успешно получен и декодирован")
                        return json.loads(decompressed)
                    else:
                        logger.error(f"Не удалось получить результат задачи. Код ответа: {response.status}")
                        raise Exception(f"Не удалось получить результат задачи: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка при получении результата задачи: {str(e)}")
            raise

    async def run_async_sync(self, endpoint):
        """
        Выполняет полный цикл асинхронной синхронизации для заданного эндпоинта.

        :param endpoint: Конечная точка API
        :return: Обработанные данные
        """
        logger.info(f"Начало асинхронной синхронизации для эндпоинта: {endpoint}")
        try:
            status_url, result_url = await self.create_async_task(endpoint)
            if not status_url or not result_url:
                raise Exception("Не удалось создать асинхронную задачу")

            while True:
                status = await self.check_task_status(status_url)
                if status['status'] == 'COMPLETED':
                    logger.info(f"Задача для эндпоинта {endpoint} завершена успешно")
                    break
                elif status['status'] == 'ERROR':
                    logger.error(f"Асинхронная задача завершилась с ошибкой: {status.get('errors')}")
                    raise Exception(f"Асинхронная задача завершилась с ошибкой: {status.get('errors')}")

            raw_data = await self.get_task_result(result_url)

            # Сохранение сырых данных
            raw_filename = os.path.join(settings.RAW_DATA_DIR, f"{endpoint.replace('/', '_')}-raw.json")
            with open(raw_filename, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)

            # Архивирование сырых данных
            archive_filename = os.path.join(settings.ARCHIVE_DIR, f"{endpoint.replace('/', '_')}-raw.gz")
            with gzip.open(archive_filename, 'wt', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Сырые данные сохранены в {raw_filename} и архивированы в {archive_filename}")

            return raw_data
        except Exception as e:
            logger.error(f"Ошибка в процессе асинхронной синхронизации: {str(e)}")
            raise
