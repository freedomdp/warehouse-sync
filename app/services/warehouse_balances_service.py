import aiohttp
import asyncio
from fastapi import HTTPException
from app.utils.utils import logger
from app.services.auth import auth_service
from app.config import settings

class WarehouseBalancesService:
    def __init__(self):
        self.base_url = settings.MY_SKLAD_API_URL
        self.max_retries = 3
        self.retry_delay = 5

    async def get_warehouse_balances(self):
        endpoint = "report/stock/bystore"
        logger.info(f"Начало получения данных об остатках по складам для эндпоинта: {endpoint}")
        all_data = []
        offset = 0
        limit = 1000

        while True:
            url = f"{self.base_url}/{endpoint}?offset={offset}&limit={limit}"
            headers = await auth_service.get_auth_header()
            logger.info(f"Запрос к URL: {url}")

            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                all_data.extend(data.get('rows', []))
                                logger.info(f"Получено {len(data.get('rows', []))} записей. Всего: {len(all_data)}")
                                if len(data.get('rows', [])) < limit:
                                    return self.process_warehouse_balances(all_data)
                                offset += limit
                                break
                            elif response.status == 401:
                                logger.warning("Получен код 401, попытка обновления токена")
                                await auth_service.refresh_token()
                                headers = await auth_service.get_auth_header()
                            else:
                                logger.error(f"Неожиданный код ответа: {response.status}")
                                raise HTTPException(status_code=response.status, detail="Ошибка при получении данных от API МойСклад")
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Попытка {attempt + 1} не удалась. Повтор через {self.retry_delay} секунд...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        logger.error(f"Ошибка при получении данных об остатках по складам: {str(e)}")
                        return self.process_warehouse_balances(all_data)  # Обрабатываем частичные данные

    def process_warehouse_balances(self, raw_data):
        logger.info("Начало обработки данных об остатках по складам")
        processed_data = []
        for item in raw_data:
            if isinstance(item, dict):
                processed_item = {
                    'id': self.extract_id_from_url(item.get('meta', {}).get('href', '')),
                    'store': ', '.join([store['name'] for store in item.get('stockByStore', []) if store.get('stock', 0) > 0])
                }
                processed_data.append(processed_item)
            else:
                logger.warning(f"Некорректный формат элемента в raw_data: {item}")
        logger.info(f"Обработка завершена. Обработано {len(processed_data)} элементов")
        return processed_data

    def extract_id_from_url(self, url):
        if not isinstance(url, str):
            logger.warning(f"Некорректный формат URL: {url}")
            return ''
        parts = url.split('/')
        return parts[-1].split('?')[0] if parts else ''

warehouse_balances_service = WarehouseBalancesService()
