import json
import requests
from woocommerce import API
from app.utils.utils import logger

class WooService:
    def __init__(self, config):
        self.wcapi = API(
            url=config.WOO_URL,
            consumer_key=config.WOO_CONSUMER_KEY,
            consumer_secret=config.WOO_CONSUMER_SECRET,
            version=config.WOO_VERSION
        )
        self.config = config

    def get_product_from_json(self, code):
        try:
            with open(self.config.JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                products = json.load(f)
            return next((p for p in products if p['code'] == code), None)
        except Exception as e:
            logger.error(f"Error reading JSON file: {str(e)}")
            return None

    def prepare_woo_product_data(self, product):
        return {
            'name': product['name'],
            'type': 'simple',
            'regular_price': str(product['salePrice']),
            'short_description': product['description'],  # Изменено с 'description' на 'short_description'
            'sku': product['code'],
            'manage_stock': True,
            'stock_quantity': int(product['stock']) if product['stock'] else 0,
            'stock_status': 'instock' if int(product['stock']) >= 1 else 'onbackorder',
        }

    async def update_or_create_product_by_code(self, code):
        product = self.get_product_from_json(code)
        if not product:
            logger.error(f"Product with code {code} not found in JSON file")
            return None

        woo_product_data = self.prepare_woo_product_data(product)

        existing_product = await self.get_product_by_sku(product['code'])

        if existing_product:
            updated_product = await self.update_product(existing_product['id'], woo_product_data)
            if updated_product:
                logger.info(f"Product with code {code} updated successfully")
                self.generate_xml(product)
                self.generate_json(product)
                return updated_product
            else:
                logger.error(f"Failed to update product with code {code}")
                return None
        else:
            new_product = await self.create_product(woo_product_data)
            if new_product:
                logger.info(f"Product with code {code} created successfully")
                self.generate_xml(product)
                self.generate_json(product)
                return new_product
            else:
                logger.error(f"Failed to create product with code {code}")
                return None

    async def get_product_by_sku(self, sku):
        try:
            response = self.wcapi.get(f"products?sku={sku}")
            if response.status_code == 200:
                products = response.json()
                if products:
                    return products[0]
            return None
        except Exception as e:
            logger.error(f"Error getting product by SKU: {str(e)}")
            return None

    async def update_product(self, product_id, data):
        try:
            response = self.wcapi.put(f"products/{product_id}", data)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return None

    async def create_product(self, data):
        try:
            response = self.wcapi.post("products", data)
            logger.info(f"Create product response status: {response.status_code}")
            logger.info(f"Create product response content: {response.json()}")
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Failed to create product. Status code: {response.status_code}")
                logger.error(f"Error message: {response.json()}")
            return None
        except Exception as e:
            logger.error(f"Exception in create_product: {str(e)}")
            return None

    def generate_xml(self, product):
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<product>
    <code>{product['code']}</code>
    <name>{product['name']}</name>
    <description>{product['description']}</description>
    <price>{product['salePrice']}</price>
    <stock>{product['stock']}</stock>
</product>
"""
        file_name = f"{product['code']}.xml"
        local_path = f"./data/xml/{file_name}"  # Сохраняем локально

        try:
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            logger.info(f"XML file created locally for product {product['code']}")
        except Exception as e:
            logger.error(f"Failed to create local XML file for product {product['code']}: {str(e)}")

    def generate_json(self, product):
        file_name = f"{product['code']}.json"
        local_path = f"./data/json/{file_name}"  # Сохраняем локально

        try:
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(product, f, ensure_ascii=False, indent=4)
            logger.info(f"JSON file created locally for product {product['code']}")
        except Exception as e:
            logger.error(f"Failed to create local JSON file for product {product['code']}: {str(e)}")
