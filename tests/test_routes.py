import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.api.routes import menu
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


def test_restaurant_menu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    restaurant_data = [
        {
            "id": 1,
            "name": "Pizza Mizza",
            "cuisine": "Italian",
            "address": "42 Pepperoni Lane",
        }
    ]

    menu_data = [
        {
            "id": 2,
            "restaurant_id": 1,
            "name": "Pepperoni Pizza",
            "price": 1800,
            "available": True,
        },
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Margherita Pizza",
            "price": 1600,
            "available": True,
        },
        {
            "id": 3,
            "restaurant_id": 1,
            "name": "Garlic Bread",
            "price": 800,
            "available": False,
        },
    ]

    restaurant_path = tmp_path / "restaurants.json"
    restaurant_path.write_text(
        json.dumps(restaurant_data),
        encoding="utf-8",
    )

    menu_path = tmp_path / "menu_items.json"
    menu_path.write_text(
        json.dumps(menu_data),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        menu.restaurant_repository,
        "file_path",
        restaurant_path,
    )

    monkeypatch.setattr(
        menu.menu_repository,
        "file_path",
        menu_path,
    )

    response = client.get("/restaurants/1/menu-items")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [1, 2, 3]
    assert response.json()[2]["available"] is False


def test_restaurant_menu_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    restaurant_path = tmp_path / "restaurants.json"
    restaurant_path.write_text(
        json.dumps([{"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "1 Rd"}]),
        encoding="utf-8",
    )
    menu_path = tmp_path / "menu_items.json"
    menu_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(menu.restaurant_repository, "file_path", restaurant_path)
    monkeypatch.setattr(menu.menu_repository, "file_path", menu_path)

    response = client.get("/restaurants/1/menu-items")

    assert response.status_code == 200
    assert response.json() == []


def test_restaurant_menu_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    restaurant_path = tmp_path / "restaurants.json"
    restaurant_path.write_text("[]", encoding="utf-8")
    menu_path = tmp_path / "menu_items.json"
    menu_path.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(menu.restaurant_repository, "file_path", restaurant_path)
    monkeypatch.setattr(menu.menu_repository, "file_path", menu_path)

    response = client.get("/restaurants/999/menu-items")

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}

@pytest.mark.parametrize("restaurant_id", ["abc", "0", "-1"])
def test_invalid_menu_restaurant_id(restaurant_id: str) -> None:
    response = client.get(f"/restaurants/{restaurant_id}/menu-items")

    assert response.status_code == 422
    
@pytest.fixture
def menu_item_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    restaurant_data = [
        {"id": 1, "name": "Pizza Mizza", "cuisine": "Italian", "address": "42 Pepperoni Lane"},
        {"id": 2, "name": "Taco Town", "cuisine": "Mexican", "address": "7 Salsa St"},
    ]
    menu_data = [
        {"id": 1, "restaurant_id": 1, "name": "Margherita Pizza", "price": 1600, "available": True},
        {"id": 2, "restaurant_id": 2, "name": "Tacos al Pastor", "price": 1400, "available": False},
    ]

    restaurant_path = tmp_path / "restaurants.json"
    restaurant_path.write_text(json.dumps(restaurant_data), encoding="utf-8")
    menu_path = tmp_path / "menu_items.json"
    menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

    monkeypatch.setattr(menu.restaurant_repository, "file_path", restaurant_path)
    monkeypatch.setattr(menu.menu_repository, "file_path", menu_path)

    return menu_data


def test_menu_item(menu_item_files) -> None:
    response = client.get("/restaurants/1/menu-items/1")

    assert response.status_code == 200
    assert response.json() == menu_item_files[0]


def test_menu_item_unavailable_is_returned(menu_item_files) -> None:
    response = client.get("/restaurants/2/menu-items/2")

    assert response.status_code == 200
    assert response.json()["available"] is False


def test_menu_item_unknown_restaurant(menu_item_files) -> None:
    response = client.get("/restaurants/999/menu-items/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


def test_menu_item_unknown_item(menu_item_files) -> None:
    response = client.get("/restaurants/1/menu-items/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Menu item not found"}


def test_menu_item_from_another_restaurant(menu_item_files) -> None:
    # Item 2 exists, but it belongs to restaurant 2
    response = client.get("/restaurants/1/menu-items/2")

    assert response.status_code == 404
    assert response.json() == {"detail": "Menu item not found"}


@pytest.mark.parametrize(
    "path",
    [
        "abc/menu-items/1",
        "0/menu-items/1",
        "-1/menu-items/1",
        "1/menu-items/abc",
        "1/menu-items/0",
        "1/menu-items/-1",
    ],
)
def test_menu_item_invalid_ids(path: str) -> None:
    response = client.get(f"/restaurants/{path}")

    assert response.status_code == 422


def test_menu_item_does_not_modify_data(tmp_path, menu_item_files) -> None:
    menu_path = menu.menu_repository.file_path
    before = Path(menu_path).read_bytes()

    client.get("/restaurants/1/menu-items/1")

    assert Path(menu_path).read_bytes() == before

def test_add_menu_item(menu_item_files):
    response = client.post(
        "/restaurants/1/menu-items",
        json={"name": "Calzone", "price": 1700},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["restaurant_id"] == 1
    assert body["name"] == "Calzone"
    assert body["available"] is True
    assert client.get(f"/restaurants/1/menu-items/{body['id']}").status_code == 200


def test_add_menu_item_unknown_restaurant(menu_item_files):
    response = client.post("/restaurants/999/menu-items", json={"name": "X", "price": 100})
    assert response.status_code == 404


@pytest.mark.parametrize("body", [
    {},
    {"name": "", "price": 100},
    {"name": "X", "price": 0},
    {"name": "X", "price": -5},
    {"name": "X", "price": "abc"},
])
def test_add_menu_item_invalid_body(menu_item_files, body):
    assert client.post("/restaurants/1/menu-items", json=body).status_code == 422

def test_update_menu_item(menu_item_files):
    response = client.patch("/restaurants/1/menu-items/1", json={"price": 1900})

    assert response.status_code == 200
    assert response.json() == {**menu_item_files[0], "price": 1900}
    assert client.get("/restaurants/1/menu-items/1").json()["price"] == 1900


def test_update_menu_item_availability(menu_item_files):
    response = client.patch("/restaurants/2/menu-items/2", json={"available": True})

    assert response.status_code == 200
    assert response.json()["available"] is True


def test_update_menu_item_unknown_restaurant(menu_item_files):
    response = client.patch("/restaurants/999/menu-items/1", json={"price": 100})

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


def test_update_menu_item_unknown_item(menu_item_files):
    response = client.patch("/restaurants/1/menu-items/999", json={"price": 100})

    assert response.status_code == 404
    assert response.json() == {"detail": "Menu item not found"}


def test_update_menu_item_from_another_restaurant(menu_item_files):
    response = client.patch("/restaurants/1/menu-items/2", json={"price": 100})

    assert response.status_code == 404
    assert response.json() == {"detail": "Menu item not found"}


@pytest.mark.parametrize("body", [
    {"name": ""},
    {"price": 0},
    {"price": -5},
    {"price": "abc"},
])
def test_update_menu_item_invalid_body(menu_item_files, body):
    assert client.patch("/restaurants/1/menu-items/1", json=body).status_code == 422