import pytest
import os
from app.services.sync.data_retrieval_service import DataRetrievalService

@pytest.mark.asyncio
async def test_fetch_products():
    service = DataRetrievalService()
    products = await service.fetch_all_products()
    assert len(products) > 0
    assert "id" in products[0]
    assert "name" in products[0]

@pytest.mark.asyncio
async def test_save_raw_data():
    service = DataRetrievalService()
    test_data = [{"id": "1", "name": "Test Product"}]
    await service.save_raw_data(test_data)

    assert os.path.exists('app/data/raw_products.json')

    # Очистка после теста
    os.remove('app/data/raw_products.json')
