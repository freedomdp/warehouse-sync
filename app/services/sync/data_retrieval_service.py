import httpx
import json
import os
import asyncio
from app.services.sync.auth_service import AuthService
from app.utils.utils import logger, check_memory_usage, handle_memory_overflow
from app.config.config import settings

class DataRetrievalService:
    def __init__(self):
        self.auth_service = AuthService()
        self.base_url = f"{self.auth_service.base_url}/entity/product"
        self.output_file = settings.OUTPUT_FILE
        self.batch_size = settings.BATCH_SIZE

    async def fetch_all_products(self):
        offset = 0
        total_products = 0
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump([], f)

        while settings.TOTAL_PRODUCTS == 0 or total_products < settings.TOTAL_PRODUCTS:
            try:
                products = await self.fetch_products_batch(offset, self.batch_size)
                if not products:
                    break
                total_products += len(products)
                await self.save_products_to_file(products)
                logger.info(f"Fetched and saved {total_products} products in total")
                if len(products) < self.batch_size:
                    break
                offset += len(products)

                if check_memory_usage(settings.MEMORY_THRESHOLD):
                    logger.warning("High memory usage detected.")
                    self.batch_size = await handle_memory_overflow(self.output_file, self.batch_size)
                    if self.batch_size == 2:
                        logger.error("Достигнут минимальный размер партии. Прерывание синхронизации.")
                        break

                await asyncio.sleep(settings.REQUEST_DELAY)

            except httpx.RequestError as e:
                logger.error(f"HTTP request error when fetching products: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error when fetching products: {e}")
                raise

        return total_products

    async def fetch_products_batch(self, offset, limit):
        logger.debug(f"Fetching products batch: offset={offset}, limit={limit}")
        auth_header = self.auth_service.get_auth_header()
        url = f"{self.base_url}?offset={offset}&limit={limit}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=auth_header)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Fetched {len(data.get('rows', []))} products in this batch")
                return data.get('rows', [])
            except httpx.RequestError as e:
                logger.error(f"HTTP request error: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error status: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

    async def save_products_to_file(self, products):
        try:
            with open(self.output_file, 'r+') as f:
                file_data = json.load(f)
                file_data.extend(products)
                f.seek(0)
                json.dump(file_data, f, indent=2)
                f.truncate()
            logger.info(f"Saved {len(products)} products to file. Total products in file: {len(file_data)}")
        except Exception as e:
            logger.error(f"Error saving products to file: {e}")
            raise
