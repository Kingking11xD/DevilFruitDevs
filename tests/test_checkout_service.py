import json
from pathlib import Path

import pytest
from app.services.checkout_service import (
    CheckoutService, InactiveCustomerError, MissingAddressError, NoActiveCartError,
    TotalChangedError, UnavailableItemError)

NOW = "2026-11-15T18:00:00Z"
CART_TOTAL = 2900

def write_json(path: Path, data) -> None:
    """Write JSON test data to a file."""
    path.write_text(json.dumps(data), encoding="utf-8")

def read_json(path: Path):
    """Read JSON data from a file."""
    return json.loads(path.read_text(encoding="utf-8"))

@pytest.fixture
def files(tmp_path: Path) -> dict[str, Path]:
    """Create isolated data files with one customer, one restaurant and an active cart."""
    paths = {
        "shopping": tmp_path / "shopping.json",
        "accounts": tmp_path / "accounts.json",
        "restaurants": tmp_path / "restaurants.json",
        "menu_items": tmp_path / "menu_items.json",
    }
    write_json(paths["accounts"], [
        {"id": 1, "name": "Ana Lopez", "role": "customer", "active": True,
         "delivery_address": "123 Test St"},
    ])
    write_json(paths["restaurants"], [
        {"id": 1, "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"},
        {"id": 2, "name": "Other Place", "cuisine": "Pizza", "address": "Grand Line"},
    ])
    write_json(paths["menu_items"], [
        {"id": 1, "restaurant_id": 1, "name": "Burger", "price": 1250, "available": True},
        {"id": 2, "restaurant_id": 1, "name": "Fries", "price": 400, "available": True},
        {"id": 3, "restaurant_id": 2, "name": "Pizza", "price": 900, "available": True},
    ])
    write_json(paths["shopping"], {
        "carts": [{
            "id": 5,
            "customer_id": 1,
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {"menu_item_id": 1, "quantity": 2},
                {"menu_item_id": 2, "quantity": 1},
            ],
        }],
        "orders": [],
    })
    return paths


def make_service(files: dict[str, Path]) -> CheckoutService:
    """Create a checkout service over the isolated files with a fixed clock."""
    return CheckoutService(
        shopping_path=files["shopping"],
        accounts_path=files["accounts"],
        restaurants_path=files["restaurants"],
        menu_items_path=files["menu_items"],
        clock=lambda: NOW,
    )


def update_file(path: Path, change) -> None:
    """Load a JSON file, change it and save it again."""
    data = read_json(path)
    change(data)
    write_json(path, data)


def test_checkout_creates_order_and_closes_cart(files: dict[str, Path]) -> None:
    """Test that a valid cart becomes a saved order and the cart is closed."""
    order = make_service(files).checkout(1, CART_TOTAL)

    assert order["id"] == 1
    assert order["source_cart_id"] == 5
    assert order["customer_name"] == "Ana Lopez"
    assert order["restaurant_name"] == "Baratie"
    assert order["delivery_address"] == "123 Test St"
    assert order["created_at"] == NOW
    assert order["items"] == [
        {"menu_item_id": 1, "name": "Burger", "unit_price": 1250, "quantity": 2, "line_total": 2500},
        {"menu_item_id": 2, "name": "Fries", "unit_price": 400, "quantity": 1, "line_total": 400},
    ]
    assert order["subtotal"] == 2900
    assert order["total"] == 2900

    saved = read_json(files["shopping"])
    assert saved["orders"] == [order]
    assert saved["carts"][0]["status"] == "closed"


def test_checkout_uses_current_menu_prices(files: dict[str, Path]) -> None:
    """Test that a price change before checkout is rejected and nothing is saved."""
    update_file(files["menu_items"], lambda items: items[0].update(price=1500))
    before = files["shopping"].read_bytes()
    with pytest.raises(TotalChangedError) as error:
        make_service(files).checkout(1, CART_TOTAL)
    assert error.value.total == 3400 
    assert files["shopping"].read_bytes() == before


def test_order_snapshot_survives_later_changes(files: dict[str, Path]) -> None:
    """Test that later menu and address changes don't rewrite a saved order."""
    order = make_service(files).checkout(1, CART_TOTAL)
    update_file(files["menu_items"], lambda items: items[0].update(price=9999, name="New Burger"))
    update_file(files["accounts"], lambda accounts: accounts[0].update(delivery_address="456 New Rd"))

    saved = read_json(files["shopping"])["orders"][0]

    assert saved == order
    assert saved["items"][0]["unit_price"] == 1250
    assert saved["delivery_address"] == "123 Test St"


@pytest.mark.parametrize(
    "change, error",
    [
        (lambda a: a[0].update(active=False), InactiveCustomerError),
        (lambda a: a[0].update(delivery_address=None), MissingAddressError),
    ],
)
def test_checkout_rejects_invalid_customer(files: dict[str, Path], change, error) -> None:
    """Test that a deactivated, missing or address-less customer can't check out."""
    update_file(files["accounts"], change)
    before = files["shopping"].read_bytes()

    with pytest.raises(error):
        make_service(files).checkout(1,  CART_TOTAL)

    assert files["shopping"].read_bytes() == before


@pytest.mark.parametrize(
    "file_name, change",
    [
        ("menu_items", lambda items: items[1].update(available=False)),  # Item became unavailable
        ("menu_items", lambda items: items[1].update(active=False)),  # Item was deactivated
        ("restaurants", lambda restaurants: restaurants[0].update(active=False)),  # Restaurant was deactivated
    ],
)
def test_checkout_rejects_unavailable_items(files: dict[str, Path], file_name: str, change) -> None:
    """Test that checkout rechecks availability and leaves the cart and orders unchanged."""
    update_file(files[file_name], change)
    before = files["shopping"].read_bytes()

    with pytest.raises(UnavailableItemError):
        make_service(files).checkout(1, CART_TOTAL)

    assert files["shopping"].read_bytes() == before

def test_checkout_only_uses_own_cart(files: dict[str, Path]) -> None:
    """Test that one customer's checkout never uses another customer's cart."""
    update_file(files["accounts"], lambda accounts: accounts.append(
        {"id": 2, "name": "Ben", "role": "customer", "active": True, "delivery_address": "9 Elm St"}))

    with pytest.raises(NoActiveCartError):
        make_service(files).checkout(2, CART_TOTAL)

    assert read_json(files["shopping"])["carts"][0]["status"] == "active"