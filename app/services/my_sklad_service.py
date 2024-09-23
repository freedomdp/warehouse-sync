import requests
import base64
import os
from fastapi import HTTPException

class MySkladService:
    def __init__(self):
        self.base_url = os.getenv("MY_SKLAD_API_URL")
        self.login = os.getenv("MY_SKLAD_LOGIN")
        self.password = os.getenv("MY_SKLAD_PASSWORD")

    def get_auth_header(self):
        credentials = f"{self.login}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}

    def get_products(self):
        url = f"{self.base_url}/entity/product"
        headers = self.get_auth_header()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("rows", [])
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Error fetching products from MoySklad: {str(e)}")
