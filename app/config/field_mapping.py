FIELD_MAPPING = {
    "id": "external_id",
    "name": "name",
    "description": "description",
    "code": "code",
    "article": "article",
    "salePrices": "sale_price",
    "updated": "updated_at",
    "pathName": "pathName"
}

def map_product(product):
    mapped_product = {}
    for source_key, target_key in FIELD_MAPPING.items():
        if source_key in product:
            if source_key == "salePrices":
                sale_prices = product[source_key]
                if sale_prices and len(sale_prices) > 0:
                    mapped_product[target_key] = sale_prices[0].get("value")
                else:
                    mapped_product[target_key] = None
            else:
                mapped_product[target_key] = product[source_key]
    return mapped_product
