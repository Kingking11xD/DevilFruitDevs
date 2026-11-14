import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep

import pytest

from app.repositories.json_store import (
    data_path,
    read_records,
    update_records,
    update_shopping,
)
from app.repositories.restaurant_repo import RestaurantRepo
from app.repositories.menu_repo import MenuRepo
from app.repositories.cart_repo import CartRepo


def test_get_all_restaurants(tmp_path):
    expected = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
        {"id": 3, "name": "Burger", "cuisine": "South Canada", "address": "20 Main St"}
    ]

    temp_path = tmp_path / "restaurants.json"
    temp_path.write_text(json.dumps(expected), encoding="utf-8")

    repository = RestaurantRepo(temp_path)
    result = repository.get_all()

    assert result == expected  # Does the loaded data match what we saved?


def test_invalid_json(tmp_path):
    temp_path = tmp_path / "invalid.json"
    temp_path.write_text("Large bags heavy bags danger cats", encoding="utf-8")

    repository = RestaurantRepo(temp_path)

    with pytest.raises(json.JSONDecodeError):
        repository.get_all()


def test_missing_file(tmp_path):
    repository = RestaurantRepo(tmp_path / "top-banana.json")
    # File is never written

    with pytest.raises(FileNotFoundError):
        repository.get_all()


def test_get_by_id(tmp_path: Path) -> None:
    data = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
    ]
    file_path = tmp_path / "restaurants.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    repository = RestaurantRepo(file_path)

    assert repository.get_by_id(2) == data[1]
    assert repository.get_by_id(999) is None


def test_get_menu_by_restaurant_id(tmp_path: Path) -> None:
    data = [
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Margherita Pizza",
            "price": 1600,
            "available": True,
        },
        {
            "id": 2,
            "restaurant_id": 2,
            "name": "Tacos al Pastor",
            "price": 1400,
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

    file_path = tmp_path / "menu_items.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    repository = MenuRepo(file_path)

    result = repository.get_by_restaurant_id(1)

    assert result == [data[0], data[2]]
    assert repository.get_by_restaurant_id(999) == []


def test_menu_get_by_id(tmp_path: Path) -> None:
    data = [
        {"id": 1, "restaurant_id": 1, "name": "Pizza", "price": 1600, "available": True},
    ]
    file_path = tmp_path / "menu_items.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    repository = MenuRepo(file_path)

    assert repository.get_by_id(1) == data[0]
    assert repository.get_by_id(999) is None


def test_menu_repo_missing_file(tmp_path: Path) -> None:
    repository = MenuRepo(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        repository.get_all()


def test_menu_repo_default_path_uses_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    assert MenuRepo().file_path == tmp_path / "menu_items.json"

def test_menu_repo_create_assigns_next_id(tmp_path):
    path = tmp_path / "menu_items.json"
    path.write_text("[]")
    repo = MenuRepo(path)
    first = repo.create(1, {"name": "Soup", "price": 500, "available": True})
    second = repo.create(2, {"name": "Tea", "price": 200, "available": True})
    assert first["id"] == 1
    assert second["id"] == 2
    assert len(repo.get_all()) == 2
    assert first["active"] is True
    assert second["active"] is True
    assert repo.get_by_id(1)["active"] is True

def test_menu_repo_update(tmp_path):
    path = tmp_path / "menu_items.json"
    path.write_text(
        json.dumps([{"id": 1, "restaurant_id": 1, "name": "A", "price": 100, "available": True}])
    )
    repo = MenuRepo(path)
    updated = repo.update(1, {"price": 250})
    assert updated["price"] == 250
    assert updated["name"] == "A"
    assert repo.get_by_id(1)["price"] == 250
    assert repo.update(99, {"price": 1}) is None


def test_menu_repo_update_invalid_saved_data(tmp_path: Path) -> None:
    """Test that invalid saved menu data is not modified."""
    path = tmp_path / "menu_items.json"
    data = [
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Pizza",
            "price": 100,
            "available": "yes",
        }
    ]
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()

    repo = MenuRepo(path)

    with pytest.raises(ValueError):
        repo.update(1, {"active": False})

    assert path.read_bytes() == before


def test_save_records(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text('[{"id": 1}]', encoding="utf-8")  # Start with one saved record

    def add_restaurant(records: list[dict]) -> None:
        records.append({"id": 2})

    update_records(path, add_restaurant)  # Add and save the new record

    assert read_records(path) == [{"id": 1}, {"id": 2}]  # Both records are still there


def test_invalid_structure(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text("{}", encoding="utf-8")  # Valid json but not a list

    with pytest.raises(ValueError):
        read_records(path)


def test_failed_save_keeps_data(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text('[{"id": 1}]', encoding="utf-8")
    before = path.read_bytes()  # Keep the original contents to compare

    def add_invalid_record(records: list[dict]) -> None:
        records.append({"value": object()})  # cannot be saved as json

    with pytest.raises(TypeError):
        update_records(path, add_invalid_record)

    assert path.read_bytes() == before  # Original data unchanged
    assert list(tmp_path.iterdir()) == [path]  # No temporary file left


def test_concurrent_updates(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text("[]", encoding="utf-8")

    def add_restaurant(number: int) -> None:
        def change(records: list[dict]) -> None:
            sleep(0.01)  # Give other updates time to overlap
            records.append({"id": number})

        update_records(path, change)

    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(add_restaurant, [1, 2]))  # Run both updates

    records = read_records(path)
    assert sorted(record["id"] for record in records) == [1, 2]  # Neither update was lost


def test_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    assert data_path("restaurants.json") == tmp_path / "restaurants.json"

def test_create_cart(tmp_path: Path) -> None:
    """Test that a new shopping cart is created and saved correctly."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)
    cart, created = repo.create(customer_id=1)

    assert created is True
    assert cart == {
        "id": 1,
        "customer_id": 1,
        "restaurant_id": None,
        "status": "active",
        "items": [],
    }

    saved_data = json.loads(path.read_text(encoding="utf-8"))
    assert saved_data["carts"] == [cart]
    assert saved_data["orders"] == []

def test_create_cart_returns_existing_active_cart(tmp_path: Path) -> None:
    """Test that a customer cannot have more than one active cart."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)

    first_cart, first_created = repo.create(customer_id=1)
    second_cart, second_created = repo.create(customer_id=1)

    assert first_created is True
    assert second_created is False
    assert first_cart == second_cart
    assert len(repo.get_all()) == 1
    assert repo.get_active_for_customer(1) == first_cart

def test_create_cart_after_closed_cart(tmp_path: Path) -> None:
    """Test that a customer can create a new cart after closing the previous one."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)

    first_cart, first_created = repo.create(customer_id=1)
    repo.update(first_cart["id"], {"status": "closed"})

    second_cart, second_created = repo.create(customer_id=1)

    assert first_created is True
    assert second_created is True
    assert second_cart["id"] == 2
    assert second_cart["customer_id"] == 1
    assert second_cart["status"] == "active"
    assert len(repo.get_all()) == 2
    assert repo.get_by_id(1)["status"] == "closed"
    assert repo.get_active_for_customer(1) == second_cart

def test_cart_get_by_id(tmp_path: Path) -> None:
    """Test retrieving a cart by ID and handling a missing cart."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)

    first_cart, _ = repo.create(customer_id=1)
    second_cart, _ = repo.create(customer_id=2)

    assert repo.get_by_id(1) == first_cart
    assert repo.get_by_id(2) == second_cart
    assert repo.get_by_id(999) is None

def test_cart_get_active_for_customer(tmp_path: Path) -> None:
    """Test finding a customer's active cart while ignoring other carts."""
    carts = [
        {
            "id": 1,
            "customer_id": 1,
            "restaurant_id": 2,
            "status": "closed",
            "items": [],
        },
        {
            "id": 2,
            "customer_id": 1,
            "restaurant_id": None,
            "status": "active",
            "items": [],
        },
        {
            "id": 3,
            "customer_id": 2,
            "restaurant_id": None,
            "status": "active",
            "items": [],
        },
    ]

    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": carts, "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)

    assert repo.get_active_for_customer(1) == carts[1]
    assert repo.get_active_for_customer(2) == carts[2]
    assert repo.get_active_for_customer(3) is None

def test_cart_repo_update(tmp_path: Path) -> None:
    """Test updating a cart while keeping other data unchanged."""
    cart = {
        "id": 1,
        "customer_id": 1,
        "restaurant_id": None,
        "status": "active",
        "items": [],
    }
    orders = [{"id": 1, "cart_id": 99}]

    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [cart], "orders": orders}),
        encoding="utf-8",
    )

    repo = CartRepo(path)
    updated = repo.update(1, {"restaurant_id": 2})

    assert updated["restaurant_id"] == 2
    assert updated["customer_id"] == 1
    assert updated["status"] == "active"
    assert updated["items"] == []
    assert repo.get_by_id(1) == updated
    assert repo.update(999, {"restaurant_id": 3}) is None

    saved_data = json.loads(path.read_text(encoding="utf-8"))
    assert saved_data["orders"] == orders

def test_cart_repo_missing_file(tmp_path: Path) -> None:
    """Test that reading a missing shopping file raises an error."""
    repo = CartRepo(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        repo.get_all()

def test_cart_repo_invalid_structure(tmp_path: Path) -> None:
    """Test that an invalid shopping data structure raises an error."""
    path = tmp_path / "shopping.json"
    path.write_text("[]", encoding="utf-8")

    repo = CartRepo(path)

    with pytest.raises(ValueError):
        repo.get_all()

@pytest.mark.parametrize(
    "shopping",
    [
        {"carts": []},
        {"carts": [], "orders": [], "extra": []},
        {"carts": "hello", "orders": []},
        {"carts": [1], "orders": []},
        {"carts": [], "orders": [1]},
    ],
)
def test_cart_repo_invalid_shopping_data(tmp_path: Path, shopping: dict) -> None:
    """Test that shopping data with invalid fields or records is rejected."""
    path = tmp_path / "shopping.json"
    path.write_text(json.dumps(shopping), encoding="utf-8")

    repo = CartRepo(path)

    with pytest.raises(ValueError):
        repo.get_all()

def test_shopping_failed_save_keeps_data(tmp_path: Path) -> None:
    """Test that a failed shopping update does not change saved data."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": [{"id": 1}]}),
        encoding="utf-8",
    )
    before = path.read_bytes()

    def add_invalid_cart(shopping: dict) -> None:
        """Add a value that cannot be saved as JSON."""
        shopping["carts"].append({"id": object()})

    with pytest.raises(TypeError):
        update_shopping(path, add_invalid_cart)

    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]

def test_cart_repo_default_path_uses_data_dir(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the cart repository uses the configured data directory."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    assert CartRepo().file_path == tmp_path / "shopping.json"

def test_cart_repo_create_assigns_next_id(tmp_path: Path) -> None:
    """Test that a new cart gets an ID higher than all existing cart IDs."""
    carts = [
        {
            "id": 2,
            "customer_id": 1,
            "restaurant_id": None,
            "status": "closed",
            "items": [],
        },
        {
            "id": 7,
            "customer_id": 2,
            "restaurant_id": None,
            "status": "active",
            "items": [],
        },
    ]

    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": carts, "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)
    new_cart, created = repo.create(customer_id=3)

    assert created is True
    assert new_cart["id"] == 8
    assert len(repo.get_all()) == 3

@pytest.mark.parametrize(
    "customer_ids, expected_count",
    [
        ([1, 2], 2),
        ([1, 1], 1),
    ],
)
def test_cart_repo_concurrent_create(
    tmp_path: Path, customer_ids: list[int], expected_count: int
) -> None:
    """Test that simultaneous cart requests create the correct number of carts."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(repo.create, customer_ids))

    carts = repo.get_all()

    assert len(carts) == expected_count
    assert len({cart["id"] for cart in carts}) == expected_count
    assert all(cart["status"] == "active" for cart in carts)

    if customer_ids[0] == customer_ids[1]:
        assert results[0][0] == results[1][0]
        assert sorted(result[1] for result in results) == [False, True]
    else:
        assert results[0][0]["id"] != results[1][0]["id"]
        assert all(created for _, created in results)

def test_cart_repo_concurrent_modify(tmp_path: Path) -> None:
    """Test that simultaneous item changes are both saved."""
    path = tmp_path / "shopping.json"
    path.write_text(
        json.dumps({"carts": [], "orders": []}),
        encoding="utf-8",
    )

    repo = CartRepo(path)
    cart, _ = repo.create(customer_id=1)

    def add_item(menu_item_id: int) -> None:
        """Add a menu item to the latest saved cart."""
        def change(current_cart: dict) -> None:
            """Add the item to the cart's existing items."""
            current_cart["items"].append(
                {"menu_item_id": menu_item_id, "quantity": 1}
            )

        repo.modify(cart["id"], change)

    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(add_item, [5, 10]))

    saved_cart = repo.get_by_id(cart["id"])

    assert len(saved_cart["items"]) == 2
    assert sorted(
        item["menu_item_id"] for item in saved_cart["items"]
    ) == [5, 10]


@pytest.mark.parametrize(
    "changes",
    [
        {"available": False},
        {"active": False},
    ],
)
def test_menu_repo_update_status_persists(tmp_path: Path, changes):
    """Test that stauts changes are saved without modifying other items."""
    path = tmp_path / "menu_items.json"
    items = [
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Pizza",
            "price": 100,
            "available": True,
            "active": True,
        },
        {
            "id": 2,
            "restaurant_id": 1,
            "name": "Burger",
            "price": 200,
            "available": True,
            "active": True,
        },
    ]
    path.write_text(json.dumps(items), encoding="utf-8")

    repo = MenuRepo(path)
    updated = repo.update(1, changes)

    expected = {**items[0] , **changes}


@pytest.mark.parametrize(
    "field, value",
    [
        ("price", -10),
        ("price", True),
        ("name", ""),
    ],
)
def test_menu_repo_update_invalid_saved_fields(
    tmp_path: Path, field, value
) -> None:
    """Test that invalid saved fields prevent menu updates."""
    path = tmp_path / "menu_item.json"
    item = {
        "id": 1,
        "restaurant_id": 1,
        "name": "Pizza",
        "price": 100,
        "available": True,
        "active": True,
    }
    item[field] = value
    path.write_text(json.dumps([item]), encoding="utf-8")
    before = path.read_bytes()

    repo = MenuRepo(path)

    with pytest.raises(ValueError):
        repo.update(1, {"available": False})

    assert path.read_bytes() == before
