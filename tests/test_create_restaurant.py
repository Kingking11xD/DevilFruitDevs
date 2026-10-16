import pytest
from fastapi.testclient import TestClient

from app.api.routes import restaurants
from app.repositories.restaurant_repo import RestaurantRepo
from main import app

client = TestClient(app)

@pytest.fixture
def create_file(tmp_path, monkeypatch):
    path = tmp_path / "restaurants.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(restaurants.repository, "file_path", path)
    return path

def test_create_restaurant(create_file):
    data = {
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    }

    response = client.post("/restaurants", json=data)

    expected = data.copy()
    expected["id"] = 1

    assert response.status_code == 201
    assert response.json() == expected
    assert client.get("/restaurants/1").json() == expected

    second = client.post("/restaurants", json=data) # Creating another restaurant should get a different ID

    assert second.status_code == 201
    assert second.json()["id"] == 2

    saved = [expected, second.json()] # Both restaurants should appear in the list and saved file
    assert client.get("/restaurants").json() == saved
    assert RestaurantRepo(create_file).get_all() == saved


def test_create_invalid(create_file):
    data = {
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    }
    before = create_file.read_bytes()

    response = client.post("/restaurants", json={}) # All required fields are missing
    assert response.status_code == 422
    assert create_file.read_bytes() == before

    invalid_fields = [ # Try one invalid field at a time
        ("name", "   "),
        ("cuisine", "   "),
        ("address", "   "),
        ("name", None),
        ("name", 123),
        ("name", "x" * 101),
        ("cuisine", "x" * 101),
        ("address", "x" * 251),
        ("id", 99),
        ("extra", "not allowed"),
    ]

    for field, value in invalid_fields:
        invalid_data = data.copy()
        invalid_data[field] = value

        response = client.post("/restaurants", json=invalid_data)

        assert response.status_code == 422, f"Accepted invalid {field}"
        assert create_file.read_bytes() == before


def test_create_storage_error(create_file):
    create_file.unlink()

    response = client.post("/restaurants", json={
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    })

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Restaurant data could not be saved"
    }
    assert not create_file.exists()
