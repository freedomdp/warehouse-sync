from fastapi import APIRouter, HTTPException
from app.utils.utils import logger, json_to_xml
import json
import os

router = APIRouter()

@router.get("/products/{product_id}")
async def get_product_details(product_id: str):
    try:
        cleaned_file_path = os.path.join('data', 'products_cleaned.json')
        full_file_path = os.path.join('data', 'products.json')

        if not os.path.exists(cleaned_file_path) or not os.path.exists(full_file_path):
            raise FileNotFoundError("Required product files not found")

        with open(cleaned_file_path, 'r') as f:
            cleaned_products = json.load(f)

        cleaned_product = next((p for p in cleaned_products if p.get('article') == product_id), None)

        if not cleaned_product:
            raise HTTPException(status_code=404, detail="Product not found")

        with open(full_file_path, 'r') as f:
            all_products = json.load(f)

        full_product = next((p for p in all_products if p.get('article') == product_id), None)

        xml_filename = f"data/product_{product_id}.xml"
        json_to_xml([full_product], xml_filename)

        return {
            "cleaned_data": cleaned_product,
            "full_data": full_product,
            "xml_file": xml_filename
        }
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting product details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
