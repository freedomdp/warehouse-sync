from fastapi import APIRouter, HTTPException
from app.services.woo.woo_service import WooService
from app.config.woo.config_vtoman import woo_config
from app.utils.utils import logger

router = APIRouter()

vtoman_woo_service = WooService(woo_config)

@router.post("/products/{codes}")
async def update_or_create_vtoman_products(codes: str):
    logger.info(f"Received request to update/create products with codes: {codes}")

    product_codes = [code.strip() for code in codes.split(',')]
    results = []
    for code in product_codes:
        try:
            result = await vtoman_woo_service.update_or_create_product_by_code(code)
            if result:
                logger.info(f"Successfully updated/created product with code: {code}")
                results.append({"code": code, "status": "success", "message": "Product updated or created successfully"})
            else:
                logger.warning(f"Product not found or operation failed for code: {code}")
                results.append({"code": code, "status": "failed", "message": "Product not found or operation failed"})
        except Exception as e:
            logger.error(f"Error updating or creating product for code {code}: {str(e)}")
            results.append({"code": code, "status": "error", "message": str(e)})

    return {"results": results}

@router.get("/products/{code}")
async def get_product_info(code: str):
    """
    GET запрос для получения информации о товаре по артикулу (code).
    """
    logger.info(f"Received GET request for product info with code: {code}")
    try:
        product = vtoman_woo_service.get_product_from_json(code)
        if product:
            logger.info(f"Found product info for code: {code}")
            return {"message": "Product info retrieved successfully", "product": product}
        else:
            logger.warning(f"Product not found for code: {code}")
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        logger.error(f"Error retrieving product info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
