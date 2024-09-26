import pytest
from app.services.sync.sync_manager import SyncManager

@pytest.mark.asyncio
async def test_run_sync():
    manager = SyncManager()
    await manager.run_sync()

    # Проверяем, что файл с сырыми данными был создан
    assert os.path.exists('app/data/raw_products.json')
