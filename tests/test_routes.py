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

def test_restaurants_empty(tmp_path, monkeypatch):
    """Test that an empty restaurant file returns an empty list"""
    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path)

    response = client.get("/restaurants")

    assert response.status_code == 200
    assert response.json() == []

def test_restaurants_does_not_modify_data(tmp_path, monkeypatch):
    """Test that retrieving restaurants does not modify the saved data"""
    data = [
        {
            "id": 1,
            "name": "Kebab",
            "cuisine": "Turkish",
            "address": "123 Main Rd"
        }
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(data), encoding="utf-8")
    before = temp_path.read_bytes()

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path)

    response = client.get("/restaurants")

    assert response.status_code == 200
    assert temp_path.read_bytes() == before

@pytest.mark.parametrize(
    ("search", "expected_names"),
    [
        ("Sushi", ["Sushi"]),
        ("su", ["Sushi"]),
        ("SUSHI", ["Sushi"]),
        ("  sushi   ", ["Sushi"]),
        ("pizza", []),
    ],
)
def test_search_restaurants(
    tmp_path,
    monkeypatch,
    search,
    expected_names,
):
    """Test restaurant name search with different search terms"""
    data = [
        {
            "id": 1,
            "name": "Sushi",
            "cuisine": "Japanese",
            "address": "310 Science Rd",
        },
        {
            "id": 2,
            "name": "Bulgogi House",
            "cuisine": "Korean",
            "address": "105 Arts Rd",
        },
        {
            "id": 3,
            "name": "Burger King",
            "cuisine": "American",
            "address": "99 Avenue Rd",
        },
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path)

    response = client.get("/restaurants", params={"search": search})

    assert response.status_code == 200
    assert [restaurant["name"] for restaurant in response.json()] == expected_names

def test_blank_restaurant_search(tmp_path, monkeypatch):
    """Test that a blank search returns all restaurants"""
    data = [
        {
            "id": 1,
            "name": "Sushi",
            "cuisine": "Japanese",
            "address": "310 Science Rd",
        },
        {
            "id": 2,
            "name": "Bulgogi House",
            "cuisine": "Korean",
            "address": "105 Arts Rd",
        },
        {
            "id": 3,
            "name": "Burger King",
            "cuisine": "American",
            "address": "99 Avenue Rd",
        },
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path)

    response = client.get("/restaurants", params={"search": "   "})

    assert response.status_code == 200
    assert response.json() == data

CUISINE_DATA = [
    {
        "id": 1,
        "name": "Sushi",
        "cuisine": "Japanese",
        "address": "310 Science Rd",
    },
    {
        "id": 2,
        "name": "Bulgogi House",
        "cuisine": "Korean",
        "address": "105 Arts Rd",
    },
    {
        "id": 3,
        "name": "Burger King",
        "cuisine": "American",
        "address": "99 Avenue Rd",
    },
    {
        "id": 4,
        "name": "Seoul Kitchen",
        "cuisine": "Korean",
        "address": "12 Main Mall",
    },
]

@pytest.fixture
def cuisine_data(tmp_path, monkeypatch):
    """Point the restaurant repository at sample restaurant data"""
    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(CUISINE_DATA), encoding="utf-8")

    monkeypatch.setattr(restaurants.repository, "file_path", temp_path)

@pytest.mark.parametrize(
    ("params", "expected_names"),
    [
        pytest.param(
            {"cuisine": "Japanese"},
            ["Sushi"],
            id="exact-match",
        ),
        pytest.param(
            {"cuisine": "japanese"},
            ["Sushi"],
            id="case-insensitive",
        ),
        pytest.param(
            {"cuisine": "   JAPANESE    "},
            ["Sushi"],
            id="surrounding-spaces",
        ),
        pytest.param(
            {"cuisine": "Kor"},
            [],
            id="partial-does-not-match",
        ),
        pytest.param(
            {"cuisine": "Italian"},
            [],
            id="unknown-cuisine",
        ),
        pytest.param(
            {"cuisine": "Korean"},
            ["Bulgogi House", "Seoul Kitchen"],
            id="same-cuisine-all-returned",
        ),
        pytest.param(
            {"cuisine": "   "},
            ["Sushi", "Bulgogi House", "Burger King", "Seoul Kitchen"],
            id="blank-returns-all",
        ),
        pytest.param(
            {"search": "bu", "cuisine": "korean"},
            ["Bulgogi House"],
            id="search-and-cuisine",
        ),
        pytest.param(
            {"search": "Sushi", "cuisine": "Korean"},
            [],
            id="both-filters-must-match",
        ),
    ],
)
def test_filter_restaurants_by_cuisine(
    cuisine_data,
    params,
    expected_names,
):
    """Test cuisine filtering on its own and with name search"""
    response = client.get("/restaurants", params=params)

    assert response.status_code == 200
    assert [
        restaurant["name"] for restaurant in response.json()
    ] == expected_names

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