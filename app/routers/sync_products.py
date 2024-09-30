# app/routers/sync_products.py
from fastapi import APIRouter, HTTPException
from app.services.my_sklad_service import MySkladService
from app.config import settings
import json

router = APIRouter()

@router.get("/sync-products")
async def sync_products():
    try:
        my_sklad_service = MySkladService()
        products = await my_sklad_service.get_products()
        with open(settings.OUTPUT_FILE, 'w') as f:
            json.dump(products, f)
        return {"message": "Products synchronized successfully", "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
