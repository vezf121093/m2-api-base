"""Fixtures compartidas por la suite de tests."""
import pytest
from fastapi.testclient import TestClient

from main import app
from tasks import repository as tasks_repository
from users import repository


@pytest.fixture(autouse=True)
def _reset_data():
    """Cada test arranca con los datos semilla y no contamina a los demás."""
    repository.reset()
    tasks_repository.reset()
    yield
    repository.reset()
    tasks_repository.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
