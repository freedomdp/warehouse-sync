from fastapi import HTTPException
import httpx
from app.services.sync.auth_service import AuthService

class MySkladService:
    def __init__(self):
        self.auth_service = AuthService()
        self.base_url = self.auth_service.base_url

    async def get_products(self):
        url = f"{self.base_url}/entity/product"
        headers = self.auth_service.get_auth_header()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("rows", [])
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"Error fetching products from MoySklad: {str(e)}")
