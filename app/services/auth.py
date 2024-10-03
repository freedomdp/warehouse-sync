import base64
import aiohttp
from app.config import settings
from app.utils.utils import logger

class AuthService:
    """
    Сервис для аутентификации и работы с токенами доступа к API МойСклад.
    """

    def __init__(self):
        """
        Инициализация сервиса аутентификации.
        """
        self.base_url = settings.MY_SKLAD_API_URL
        self.token = None

    def get_basic_auth_header(self):
        """
        Генерирует заголовок для Basic Auth.

        :return: Строка заголовка Basic Auth
        """
        credentials = f"{settings.MY_SKLAD_LOGIN}:{settings.MY_SKLAD_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    async def get_token(self):
        """
        Асинхронно получает токен доступа от API МойСклад.

        :return: Токен доступа
        """
        url = f"{self.base_url}/security/token"
        headers = {
            "Authorization": self.get_basic_auth_header(),
            "Accept-Encoding": "gzip"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                if response.status in [200, 201]:  # Учитываем оба кода состояния
                    data = await response.json()
                    self.token = data["access_token"]
                    logger.info("Токен доступа успешно получен")
                    return self.token
                else:
                    error_message = f"Не удалось получить токен. Код ответа: {response.status}"
                    logger.error(error_message)
                    raise Exception(error_message)

    async def get_auth_header(self):
        """
        Асинхронно возвращает заголовок авторизации с токеном.

        :return: Словарь с заголовком авторизации
        """
        if not self.token:
            await self.get_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept-Encoding": "gzip"
        }

    async def refresh_token(self):
        """
        Асинхронно обновляет токен доступа.

        :return: Новый токен доступа
        """
        logger.info("Обновление токена доступа")
        return await self.get_token()

# Создаем глобальный экземпляр сервиса аутентификации
auth_service = AuthService()
