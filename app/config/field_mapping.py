FIELD_MAPPING = {
    "id": "external_id",
    "name": "name",
    "code": "code",
    "article": "article",
    "minPrice": "min_price",
    "salePrices": "sale_price",
    "archived": "archived",
    "updated": "updated_at"
}

def map_product(product_data):
    """
    Функция для маппинга данных продукта из API в формат модели базы данных.
    """
    mapped_product = {}
    for json_field, db_field in FIELD_MAPPING.items():
        if json_field in product_data:
            if json_field == "minPrice":
                mapped_product[db_field] = product_data[json_field]["value"] / 100
            elif json_field == "salePrices":
                sale_price = next((price['value'] for price in product_data[json_field] if price['priceType'].get('name') == 'Цена продажи'), None)
                mapped_product[db_field] = sale_price / 100 if sale_price else None
            else:
                mapped_product[db_field] = product_data[json_field]
    return mapped_product
