import psutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.sync.sync_manager import SyncManager
from app.utils.utils import logger
from app.config.config import settings

app = FastAPI()

global_data = {
    "products": [],
    "last_sync": None,
    "sync_status": "Не выполнялась",
    "sync_error": None
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Вывод информации о памяти
    memory = psutil.virtual_memory()
    logger.info(f"Total memory: {memory.total / (1024 * 1024):.2f} MB")
    logger.info(f"Available memory: {memory.available / (1024 * 1024):.2f} MB")
    logger.info(f"Used memory: {memory.used / (1024 * 1024):.2f} MB")
    logger.info(f"Memory usage: {memory.percent}%")

    logger.info("Запуск синхронизации с Мой склад")
    try:
        sync_manager = SyncManager()
        products = await sync_manager.run_sync()
        global_data["products"] = products
        global_data["last_sync"] = sync_manager.last_sync_time
        global_data["sync_status"] = "Успешно завершена"
        global_data["sync_error"] = None
        logger.info(f"Синхронизация завершена успешно. Получено {len(products)} товаров.")
    except Exception as e:
        global_data["sync_status"] = "Завершилась с ошибкой"
        global_data["sync_error"] = str(e)
        logger.error(f"Ошибка при выполнении синхронизации: {e}", exc_info=True)

@app.get("/")
async def root():
    logger.info("Запрошена корневая страница")
    return {"message": "My Warehouse Sync API is running"}

@app.get("/sync-status")
async def sync_status():
    logger.info("Запрошен статус синхронизации")
    return {
        "last_sync": global_data["last_sync"],
        "products_count": len(global_data["products"]),
        "sync_status": global_data["sync_status"],
        "sync_error": global_data["sync_error"]
    }

@app.get("/products")
async def get_products():
    logger.info("Запрошен список продуктов")
    if global_data["sync_error"]:
        error_message = f"Данные не были получены. Ошибка: {global_data['sync_error']}"
        logger.warning(error_message)
        raise HTTPException(status_code=503, detail=error_message)
    return {"products": global_data["products"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
