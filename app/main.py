import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.sync.sync_manager import SyncManager
from app.utils.utils import logger
from app.utils.data_processing import process_data
from app.config import settings
import psutil  # Добавим импорт psutil

app = FastAPI()

# Глобальная переменная для хранения данных о синхронизации
global_data = {
    "products": [],
    "last_sync": None,
    "sync_status": "Не выполнялась",
    "sync_error": None
}

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    Функция, выполняемая при запуске приложения.
    """
    logger.info("Начало выполнения startup_event")
    try:
        memory = psutil.virtual_memory()
        logger.info(f"Общая память: {memory.total / (1024 * 1024):.2f} MB")
        logger.info(f"Доступная память: {memory.available / (1024 * 1024):.2f} MB")
        logger.info(f"Использованная память: {memory.used / (1024 * 1024):.2f} MB")
        logger.info(f"Процент использования памяти: {memory.percent}%")

        logger.info("Запуск синхронизации с Мой склад")
        sync_manager = SyncManager()
        products = await sync_manager.run_sync()
        global_data["products"] = products
        global_data["last_sync"] = sync_manager.last_sync_time
        global_data["sync_status"] = "Успешно завершена"
        global_data["sync_error"] = None

        logger.info(f"Синхронизация завершена успешно. Получено {len(products)} товаров.")

        logger.info("Начало обработки данных")
        cleaned_json_file, xml_file = process_data()
        logger.info(f"Данные обработаны и сохранены в {cleaned_json_file} и {xml_file}")

    except Exception as e:
        global_data["sync_status"] = "Завершилась с ошибкой"
        global_data["sync_error"] = str(e)
        logger.error(f"Ошибка при выполнении синхронизации: {e}", exc_info=True)
    finally:
        logger.info("Завершение выполнения startup_event")

@app.get("/")
async def root():
    """
    Корневой эндпоинт. Возвращает статус работы API.
    """
    return {"message": "My Warehouse Sync API is running"}

@app.get("/sync-status")
async def sync_status():
    """
    Эндпоинт для получения статуса синхронизации.
    """
    return {
        "last_sync": global_data["last_sync"],
        "products_count": len(global_data["products"]),
        "sync_status": global_data["sync_status"],
        "sync_error": global_data["sync_error"]
    }

@app.get("/products")
async def get_products():
    """
    Эндпоинт для получения списка продуктов.
    """
    try:
        if global_data["sync_error"]:
            error_message = f"Данные не были получены. Ошибка: {global_data['sync_error']}"
            logger.warning(error_message)
            raise HTTPException(status_code=503, detail=error_message)
        return {"products": global_data["products"]}
    except Exception as e:
        logger.error(f"Ошибка при получении списка продуктов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/products/{article}")
async def get_product_by_article(article: str):
    """
    Эндпоинт для получения детальной информации о продукте по его артикулу.
    """
    try:
        with open(settings.OUTPUT_FILE, 'r') as f:
            products = json.load(f)

        product = next((p for p in products if p.get('article') == article), None)

        if product:
            return product
        else:
            raise HTTPException(status_code=404, detail="Продукт не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о продукте: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/categories")
async def get_categories():
    """
    Эндпоинт для получения списка уникальных категорий товаров.
    """
    try:
        with open(settings.OUTPUT_FILE.replace('.json', '_cleaned.json'), 'r') as f:
            products = json.load(f)

        # Получаем уникальные pathName
        categories = set(product.get('pathName') for product in products if product.get('pathName'))

        # Создаем структурированный список категорий
        structured_categories = {}
        for path in categories:
            parts = path.split('/')
            current = structured_categories
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        return {
            "simple_list": sorted(list(categories)),
            "structured_list": structured_categories
        }
    except Exception as e:
        logger.error(f"Ошибка при получении списка категорий: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
