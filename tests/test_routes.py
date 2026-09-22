import json

from fastapi.testclient import TestClient
from main import app
from app.api.routes import restaurants

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_restaurants(tmp_path, monkeypatch):
    expected = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican"},
        {"id": 3, "name": "Burger", "cuisine": "South Canada"}
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(expected), encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path) # restaurants.repository file_path -> temp_path then restores after the test

    response = client.get("/restaurants")
    # Test client > route > service > repository > temp JSON

    assert response.status_code == 200
    assert response.json() == expected