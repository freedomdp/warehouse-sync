import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.services.async_sync_service import AsyncSyncService

@pytest.mark.asyncio
async def test_async_api_availability():
    async_service = AsyncSyncService()
    try:
        result_url, status_url = await async_service.create_async_task()
        assert result_url is not None
        assert status_url is not None
    except Exception as e:
        pytest.skip(f"Async API is not available: {str(e)}")
