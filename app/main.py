from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import root, warehouse_stock, assortment, warehouse_balances, product_collector
from app.utils.utils import logger
import psutil

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(root.router)
app.include_router(warehouse_stock.router)
app.include_router(assortment.router)
app.include_router(warehouse_balances.router)
app.include_router(product_collector.router)

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
    except Exception as e:
        logger.error(f"Ошибка при выполнении startup_event: {e}", exc_info=True)
    finally:
        logger.info("Завершение выполнения startup_event")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
