import json

import pytest

from app.repositories.cart_repo import CartRepo
from app.repositories.menu_repo import MenuRepo
from app.services.cart_service import (
    CartNotFoundError,
    CartRestaurantMismatchError,
    CartService,
    MenuItemNotAvailableError,
)
from app.services.menu_service import MenuItemNotFoundError

@pytest.fixture
def cart_service(tmp_path):
    """Create a cart service with temporary shopping and menu data."""
    cart_file = tmp_path / "shopping.json"
    menu_file = tmp_path / "menu_items.json"

    cart_file.write_text(json.dumps({
        "carts": [],
        "orders": [],
    }))

    menu_file.write_text(json.dumps([
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Burger",
            "price": 100,
            "available": True,
            "active": True,
        },
        {
            "id": 2,
            "restaurant_id": 2,
            "name": "Pizza",
            "price": 150,
            "available": True,
            "active": True,
        },
        {
            "id": 3,
            "restaurant_id": 1,
            "name": "Fries",
            "price": 50,
            "available": False,
            "active": True,
        },
        {
            "id": 4,
            "restaurant_id": 1,
            "name": "Salad",
            "price": 80,
            "available": True,
            "active": False,
        },
    ]))

    cart_repository = CartRepo()
    cart_repository.file_path = cart_file

    menu_repository = MenuRepo()
    menu_repository.file_path = menu_file

    cart_repository.create(customer_id=1)

    return CartService(cart_repository, menu_repository)


def test_add_item_to_empty_cart(cart_service):
    """Test adding an available item to an empty cart."""
    updated_cart = cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    assert updated_cart["restaurant_id"] == 1
    assert updated_cart["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 2,
        }
    ]


def test_add_existing_item_increases_quantity(cart_service):
    """Test increasing the quantity of an existing cart item."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    updated_cart = cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=3,
    )

    assert updated_cart["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 5
        }
    ]


def test_add_unavailable_item(cart_service):
    """Test rejecting an unavailable menu item."""
    with pytest.raises(MenuItemNotAvailableError):
        cart_service.add_item(
            customer_id=1,
            menu_item_id=3,
            quantity=2,
        )


def test_add_deactivated_item(cart_service):
    """Test rejecting a deactivated menu item."""
    with pytest.raises(MenuItemNotAvailableError):
        cart_service.add_item(
            customer_id=1,
            menu_item_id=4,
            quantity=2,
        )


def test_add_nonexistent_item(cart_service):
    """Test rejecting a menu item that does not exist."""
    with pytest.raises(MenuItemNotFoundError):
        cart_service.add_item(
            customer_id=1,
            menu_item_id=55,
            quantity=2,
        )


def test_add_item_from_different_restaurant(cart_service):
    """Test rejecting items from a different restaurant."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    with pytest.raises(CartRestaurantMismatchError):
        cart_service.add_item(
            customer_id=1,
            menu_item_id=2,
            quantity=1,
        )


def test_add_item_without_active_cart(cart_service):
    """Test rejecting an item when the customer has no active cart."""
    with pytest.raises(CartNotFoundError):
        cart_service.add_item(
            customer_id=2,
            menu_item_id=1,
            quantity=2,
        )


def test_rejected_item_does_not_change_cart(cart_service):
    """Test that a rejected item leaves the saved cart unchanged."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    with pytest.raises(MenuItemNotAvailableError):
        cart_service.add_item(
            customer_id=1,
            menu_item_id=3,
            quantity=2,
        )

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)

    assert saved_cart["restaurant_id"] == 1
    assert saved_cart["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 2,
        }
    ]


def test_get_cart_details_calculates_totals(cart_service):
    """Test that cart details include correct prices and totals."""
    cart_service.add_item(
        customer_id=1, menu_item_id=1, quantity=2
    )

    result = cart_service.get_cart_details(customer_id=1)

    assert len(result["items"]) == 1
    assert result["items"][0] == {
        "menu_item_id": 1,
        "name": "Burger",
        "quantity": 2,
        "unit_price": 100,
        "line_total": 200,
        "problems": []
    }
    assert result["subtotal"] == 200
    assert result["total"] == 200
    assert result["problems"] == []


def test_get_cart_details_multiple_items(cart_service):
    """Test that totals include all items in the cart."""
    cart_service.add_item(
        customer_id=1, menu_item_id=1, quantity=2
    )

    cart_service.cart_repository.modify(
        1,
        lambda cart: cart["items"].append({
            "menu_item_id": 3,
            "quantity": 3,
        }),
    )

    result = cart_service.get_cart_details(customer_id=1)

    assert len(result["items"]) == 2
    assert result["items"][0]["line_total"] == 200
    assert result["items"][1]["line_total"] == 150
    assert result["items"][1]["problems"] == ["unavailable"]
    assert result["subtotal"] == 350
    assert result["total"] == 350
    assert result["problems"] == ["unavailable"]


def test_get_cart_details_empty_cart(cart_service):
    """Test that an empty cart has no items and zero totals."""
    result = cart_service.get_cart_details(customer_id=1)

    assert result["items"] == []
    assert result["subtotal"] == 0
    assert result["total"] == 0
    assert result["problems"] == []


def test_get_cart_details_missing_item(cart_service):
    """Test that a missing menu item is reported in cart details."""
    cart_service.cart_repository.modify(
        1,
        lambda cart: cart["items"].append({
            "menu_item_id": 999,
            "quantity": 2,
        }),
    )

    result = cart_service.get_cart_details(customer_id=1)

    assert len(result["items"]) == 1
    assert result["items"][0] == {
        "menu_item_id": 999,
        "name": None,
        "quantity": 2,
        "unit_price": None,
        "line_total": None,
        "problems": ["missing"],
    }
    assert result["subtotal"] == 0
    assert result["total"] == 0
    assert result["problems"] == ["missing"]


def test_get_cart_details_inactive_item(cart_service):
    """Test that an inactive menu item is flagged in cart details."""
    cart_service.cart_repository.modify(
        1,
        lambda cart: cart["items"].append({
            "menu_item_id": 4,
            "quantity": 2,
        }),
    )

    result = cart_service.get_cart_details(customer_id=1)

    assert len(result["items"]) == 1
    assert result["items"][0] == {
        "menu_item_id": 4,
        "name": "Salad",
        "quantity": 2,
        "unit_price": 80,
        "line_total": 160,
        "problems": ["inactive"],
    }
    assert result["subtotal"] == 160
    assert result["total"] == 160
    assert result["problems"] == ["inactive"]


def test_get_cart_details_no_active_cart(cart_service):
    """Test that a missing active cart raises an error."""
    with pytest.raises(CartNotFoundError):
        cart_service.get_cart_details(customer_id=999)
