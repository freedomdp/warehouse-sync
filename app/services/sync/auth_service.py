import base64
import httpx
from app.config import settings
from app.utils.utils import logger

class AuthService:
    def __init__(self):
        self.base_url = settings.MY_SKLAD_API_URL
        self.login = settings.MY_SKLAD_LOGIN
        self.password = settings.MY_SKLAD_PASSWORD
        logger.debug(f"AuthService initialized with base URL: {self.base_url}")

    def get_auth_header(self):
        credentials = f"{self.login}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}

    async def test_auth(self):
        logger.info("Testing authentication")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/entity/employee", headers=self.get_auth_header())
                response.raise_for_status()
                logger.info("Authentication successful")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"Authentication failed with status code {e.response.status_code}")
                raise httpx.HTTPStatusError(f"Authentication failed: {e}", request=e.request, response=e.response)
            except Exception as e:
                logger.error(f"Unexpected error during authentication: {str(e)}")
                raise
