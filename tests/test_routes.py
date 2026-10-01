import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes import restaurants
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_restaurants(tmp_path, monkeypatch):
    expected = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
        {"id": 3, "name": "Burger", "cuisine": "South Canada", "address": "20 Main St"}
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(expected), encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path) # restaurants.repository file_path -> temp_path then restores after the test

    response = client.get("/restaurants")
    # Test client > route > service > repository > temp JSON

    assert response.status_code == 200
    assert response.json() == expected


def test_restaurant_details(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
    ]

    file_path = tmp_path / "restaurants.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    before = file_path.read_bytes()

    monkeypatch.setattr(restaurants.repository, "file_path", file_path)

    response = client.get("/restaurants/2")

    assert response.status_code == 200
    assert response.json() == data[1]
    assert file_path.read_bytes() == before


def test_restaurant_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = tmp_path / "restaurants.json"
    file_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", file_path)

    response = client.get("/restaurants/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


def test_invalid_restaurant_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = tmp_path / "restaurants.json"
    file_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", file_path)

    for restaurant_id in ["abc", "0", "-1"]:
        response = client.get(f"/restaurants/{restaurant_id}")
        assert response.status_code == 422, f"Failed for ID: {restaurant_id}"