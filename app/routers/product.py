from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.product import Product
from app.services.my_sklad_service import MySkladService

router = APIRouter()

@router.get("/sync-products")
async def sync_products(db: Session = Depends(get_db)):
    try:
        my_sklad_service = MySkladService()
        products = my_sklad_service.get_products()

        for product_data in products:
            existing_product = db.query(Product).filter(Product.external_id == product_data["id"]).first()
            if existing_product:
                existing_product.name = product_data["name"]
                existing_product.price = product_data["salePrices"][0]["value"] / 100 if product_data["salePrices"] else 0
                existing_product.quantity = product_data["quantity"]
            else:
                new_product = Product(
                    external_id=product_data["id"],
                    name=product_data["name"],
                    price=product_data["salePrices"][0]["value"] / 100 if product_data["salePrices"] else 0,
                    quantity=product_data["quantity"]
                )
                db.add(new_product)

        db.commit()
        return {"message": "Products synchronized successfully", "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
