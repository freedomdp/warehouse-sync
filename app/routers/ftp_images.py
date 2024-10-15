import json
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from app.services.ftp_service import ftp_service
from app.utils.utils import logger
from app.config import settings
import io

router = APIRouter()

@router.get("/FTPimages", response_class=HTMLResponse)
async def get_ftp_images():
    """
    GET запрос. Получает сгруппированный список ссылок на изображения с FTP сервера,
    сохраняет их в JSON файл и возвращает HTML-страницу со списком.
    """
    logger.info("Начало обработки запроса GET /FTPimages")
    try:
        grouped_images = ftp_service.get_image_links()
        logger.info(f"Получено {sum(len(images) for images in grouped_images.values())} ссылок на изображения")

        # Сохранение данных в JSON файл
        json_file_path = os.path.join(settings.JSON_DIR, 'ftp_images.json')
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(grouped_images, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в JSON файл: {json_file_path}")

        html_content = "<html><body><h1>Список изображений по артикулам</h1>"
        for article, images in grouped_images.items():
            html_content += f"<h2>Артикул: {article}</h2><ul>"
            for image in images:
                html_content += f'<li><a href="{image["ftp_link"]}" target="_blank">{image["filename"]}</a></li>'
            html_content += "</ul>"
        html_content += "</body></html>"

        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Ошибка при получении ссылок на изображения: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/{filename}")
async def get_image(filename: str):
    """
    GET запрос. Получает изображение с FTP сервера и возвращает его.
    """
    try:
        image_data = ftp_service.get_image(filename)
        return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Ошибка при получении изображения {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
