import pytest
from app.services.sync.auth_service import AuthService

def test_auth_header_generation():
    auth_service = AuthService()
    header = auth_service.get_auth_header()
    assert "Authorization" in header
    assert header["Authorization"].startswith("Basic ")

@pytest.mark.asyncio
async def test_auth_success():
    auth_service = AuthService()
    assert await auth_service.test_auth() == True
