import aiohttp
import asyncio
import gzip
import json
import base64
import os
from app.config import settings
from app.utils.utils import logger

class AsyncSyncService:
    def __init__(self):
        self.base_url = settings.MY_SKLAD_API_URL
        credentials = f"{settings.MY_SKLAD_LOGIN}:{settings.MY_SKLAD_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Accept-Encoding": "gzip"
        }

    async def create_async_task(self):
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/entity/product?async=true"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 202:
                    return response.headers.get('Location'), response.headers.get('Content-Location')
                else:
                    content = await response.text()
                    logger.error(f"Failed to create async task. Status: {response.status}, Content: {content}")
                    return None, None

    async def check_task_status(self, status_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(status_url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to check task status: {response.status}")

    async def get_task_result(self, result_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(result_url, headers=self.headers) as response:
                if response.status == 200:
                    content = await response.read()
                    decompressed = gzip.decompress(content)
                    return json.loads(decompressed)
                else:
                    raise Exception(f"Failed to get task result: {response.status}")

    async def get_products_sync(self):
        all_products = []
        offset = 0
        limit = 1000  # Максимальное количество товаров на страницу

        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/entity/product?offset={offset}&limit={limit}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get products: {response.status}")

                    data = await response.json()
                    products = data.get('rows', [])
                    all_products.extend(products)

                    if len(products) < limit:
                        break  # Это была последняя страница

                    offset += limit

        return all_products

    async def save_archive(self, products):
        archive_path = os.path.join('data', 'products_archive.gz')
        with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logger.info(f"Archived products saved to {archive_path}")

    async def run_async_sync(self):
        try:
            logger.warning("Async API is not available. Using sync method.")
            products = await self.get_products_sync()
            await self.save_archive(products)
            return products
        except Exception as e:
            logger.error(f"Error in sync: {str(e)}")
            raise
