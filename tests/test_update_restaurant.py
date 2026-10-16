import json

import pytest
from fastapi.testclient import TestClient

from app.api.routes import restaurants
from app.repositories.restaurant_repo import RestaurantRepo
from main import app


client = TestClient(app)

ORIGINAL = {
    "id": 1,
    "name": "Baratie",
    "cuisine": "Seafood",
    "address": "East Blue",
}


@pytest.fixture
def update_file(tmp_path, monkeypatch):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps([ORIGINAL]), encoding="utf-8")
    monkeypatch.setattr(restaurants.repository, "file_path", path)
    return path


def test_update_restaurant(update_file):
    response = client.patch("/restaurants/1", json={
        "address": "  Water 7  ",
    })

    expected = ORIGINAL.copy()
    expected["address"] = "Water 7"

    assert response.status_code == 200
    assert response.json() == expected
    assert client.get("/restaurants/1").json() == expected
    assert RestaurantRepo(update_file).get_all() == [expected]


def test_update_invalid(update_file):
    before = update_file.read_bytes()

    invalid_updates = [
        {},
        {"name": "   "},
        {"cuisine": "   "},
        {"address": "   "},
        {"name": None},
        {"cuisine": None},
        {"address": None},
        {"name": 123},
        {"name": "x" * 101},
        {"cuisine": "x" * 101},
        {"address": "x" * 251},
        {"id": 99},
        {"extra": "value"},
        {"name": "Valid Name", "address": None},
    ]

    for changes in invalid_updates:
        response = client.patch("/restaurants/1", json=changes)

        assert response.status_code == 422, f"Accepted {changes}"
        assert update_file.read_bytes() == before


def test_update_errors(update_file):
    before = update_file.read_bytes()

    response = client.patch("/restaurants/999", json={"name": "Cafe"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}
    assert update_file.read_bytes() == before

    # A missing data file is a storage error.
    update_file.unlink()
    response = client.patch("/restaurants/1", json={"name": "Cafe"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Restaurant data not saved"}
    assert not update_file.exists()
