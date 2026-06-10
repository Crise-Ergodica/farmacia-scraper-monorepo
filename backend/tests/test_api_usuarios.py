import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import get_db
from app.core.auth import current_active_user
from app.models.usuario import Usuario
import uuid

# Setup an async mock for get_db
# This is a bit complex for a simple API validation test since we need an async engine
# For simplicity, we can mock the dependency `current_active_user` and `get_db`

# Mock DB Session
class MockAsyncSession:
    def get(self, model, id, **kwargs):
        return None  # Simulate item not found (404)

async def override_get_db():
    yield MockAsyncSession()

def override_current_active_user():
    return Usuario(id=uuid.uuid4(), email="test@precobao.com")

client = TestClient(app)

def test_add_favorito_unauthorized():
    # Attempting to access without overriding current_user should fail
    response = client.post("/users/me/favoritos/medicamentos/999")
    assert response.status_code == 401

def test_add_favorito_medicamento_not_found():
    app.dependency_overrides[current_active_user] = override_current_active_user
    app.dependency_overrides[get_db] = override_get_db

    response = client.post("/users/me/favoritos/medicamentos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Medicamento não encontrado."}

    app.dependency_overrides.clear()

def test_add_favorito_farmacia_not_found():
    app.dependency_overrides[current_active_user] = override_current_active_user
    app.dependency_overrides[get_db] = override_get_db

    response = client.post("/users/me/favoritos/farmacias/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Farmácia não encontrada."}

    app.dependency_overrides.clear()
