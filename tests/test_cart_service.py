import json

import pytest

from app.repositories.cart_repo import CartRepo
from app.repositories.menu_repo import MenuRepo
from app.services.cart_service import (
    CartItemNotFoundError,
    CartNotFoundError,
    CartRestaurantMismatchError,
    CartService,
    MenuItemNotAvailableError,
)
from app.services.menu_service import MenuItemNotFoundError
from pydantic import ValidationError

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


def test_update_item_quantity_replaces_existing_quantity(cart_service):
    """Test replacing an item's quantity instead of increasing it."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    updated_cart = cart_service.update_item_quantity(
        customer_id=1,
        menu_item_id=1,
        quantity=5,
    )

    assert updated_cart["items"] == [
        {"menu_item_id": 1, "quantity": 5}
    ]

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart["items"] == updated_cart["items"]

    details = cart_service.get_cart_details(customer_id=1)
    assert details["subtotal"] == 500
    assert details["total"] == 500


def test_update_item_quantity_invalid_quantity(cart_service):
    """Test that an invalid quantity doesn't change the saved cart."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    original_cart = cart_service.cart_repository.get_active_for_customer(1)

    with pytest.raises(ValidationError):
        cart_service.update_item_quantity(
            customer_id=1,
            menu_item_id=1,
            quantity=0,
        )

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_update_item_quantity_missing_item(cart_service):
    """Test that updating a missing item leaves the cart unchanged."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    original_cart = cart_service.cart_repository.get_active_for_customer(1)

    with pytest.raises(CartItemNotFoundError):
        cart_service.update_item_quantity(
            customer_id=1,
            menu_item_id=99,
            quantity=5,
        )

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_update_item_quantity_missing_cart(cart_service):
    """Test that updating a missing cart doesn't change stored data."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    original_cart = cart_service.cart_repository.get_active_for_customer(1)

    with pytest.raises(CartNotFoundError):
        cart_service.update_item_quantity(
            customer_id=101,
            menu_item_id=1,
            quantity=5,
        )

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_update_item_quantity_only_own_cart(cart_service):
    """Test that updating one customer's cart doesn't affect another."""
    cart_service.cart_repository.create(customer_id=2)

    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )
    cart_service.add_item(
        customer_id=2,
        menu_item_id=1,
        quantity=3,
    )

    cart_service.update_item_quantity(
        customer_id=2,
        menu_item_id=1,
        quantity=5,
    )

    cart_1 = cart_service.cart_repository.get_active_for_customer(1)
    cart_2 = cart_service.cart_repository.get_active_for_customer(2)

    assert cart_1["items"][0]["quantity"] == 2
    assert cart_2["items"][0]["quantity"] == 5


def test_update_item_quantity_invalid_saved_cart_unchanged(cart_service):
    """Test that invalid saved cart data is not modified."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cart_file = cart_service.cart_repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    with pytest.raises(ValidationError):
        cart_service.update_item_quantity(
            customer_id=1,
            menu_item_id=1,
            quantity=5,
        )

    assert cart_file.read_text() == original_data


def test_update_item_quantity_cart_closed_before_modify(
    cart_service, monkeypatch
):
    """Test that a cart closing during an update keeps its quantity."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    repo = cart_service.cart_repository
    original_modify = repo.modify

    def closed_before_modify(cart_id, change):
        """Simulate the cart closing before the quantity is updated."""
        repo.update(cart_id, {"status": "closed"})
        return original_modify(cart_id, change)

    monkeypatch.setattr(repo, "modify", closed_before_modify)

    with pytest.raises(CartNotFoundError):
        cart_service.update_item_quantity(
            customer_id=1,
            menu_item_id=1,
            quantity=5,
        )

    saved_cart = repo.get_by_id(1)
    assert saved_cart["status"] == "closed"
    assert saved_cart["items"] == [
        {"menu_item_id": 1, "quantity": 2}
    ]


def test_remove_last_cart_item(cart_service):
    """Test removing the last item resets the cart and totals."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    updated_cart = cart_service.remove_item(
        customer_id=1,
        menu_item_id=1,
    )

    assert updated_cart["items"] == []
    assert updated_cart["restaurant_id"] is None

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart["items"] == []
    assert saved_cart["restaurant_id"] is None

    details = cart_service.get_cart_details(customer_id=1)
    assert details["subtotal"] == 0
    assert details["total"] == 0


def test_remove_cart_item_keeps_other_items(cart_service):
    """Test removing one item leaves other items unchanged."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    repo = cart_service.cart_repository
    repo.modify(
        1,
        lambda cart: cart["items"].append({
            "menu_item_id": 3,
            "quantity": 3,
        }),
    )

    updated_cart = cart_service.remove_item(
        customer_id=1,
        menu_item_id=1,
    )

    expected_items = [{"menu_item_id": 3, "quantity": 3}]

    assert updated_cart["items"] == expected_items
    assert updated_cart["restaurant_id"] == 1

    saved_cart = repo.get_active_for_customer(1)
    assert saved_cart["items"] == expected_items

    details = cart_service.get_cart_details(customer_id=1)
    assert details["subtotal"] == 150
    assert details["total"] == 150


def test_remove_cart_item_not_found(cart_service):
    """Test removing a nonexistent item leaves the cart unchanged."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    repo = cart_service.cart_repository
    original_cart = repo.get_active_for_customer(1)

    with pytest.raises(CartItemNotFoundError):
        cart_service.remove_item(
            customer_id=1,
            menu_item_id=310,
        )

    saved_cart = repo.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_remove_cart_item_no_active_cart(cart_service):
    """Test removing an item when the customer has no active cart."""
    repo = cart_service.cart_repository
    original_cart = repo.get_active_for_customer(1)

    with pytest.raises(CartNotFoundError):
        cart_service.remove_item(
            customer_id=22,
            menu_item_id=1,
        )

    saved_cart = repo.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_remove_cart_item_only_own_cart(cart_service):
    """Test that removing an item only affects the customer's cart."""
    repo = cart_service.cart_repository
    repo.create(customer_id=2)

    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )
    cart_service.add_item(
        customer_id=2,
        menu_item_id=1,
        quantity=3,
    )

    cart_service.remove_item(
        customer_id=2,
        menu_item_id=1,
    )

    cart_1 = repo.get_active_for_customer(1)
    cart_2 = repo.get_active_for_customer(2)

    assert cart_1["items"] == [
        {"menu_item_id": 1, "quantity": 2}
    ]
    assert cart_2["items"] == []
    assert cart_2["restaurant_id"] is None


def test_remove_cart_item_invalid_saved_cart_unchanged(cart_service):
    """Test that invalid saved cart data is not modified."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cart_file = cart_service.cart_repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    with pytest.raises(ValidationError):
        cart_service.remove_item(
            customer_id=1,
            menu_item_id=1,
        )

    assert cart_file.read_text() == original_data


def test_remove_cart_item_duplicate_items_unchanged(cart_service):
    """Test that duplicate saved cart items are rejected."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cart_file = cart_service.cart_repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"].append({
        "menu_item_id": 1,
        "quantity": 3,
    })
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    with pytest.raises(ValueError, match="Duplicate cart items"):
        cart_service.remove_item(
            customer_id=1,
            menu_item_id=1,
        )

    assert cart_file.read_text() == original_data


def test_remove_cart_item_cart_closed_before_modify(
        cart_service, monkeypatch
):
    """Test that removing an item from a newly closed cart is rejected."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    repo = cart_service.cart_repository
    original_modify = repo.modify

    def close_before_modify(cart_id, change):
        """Simulate the cart closing before removal."""
        repo.update(cart_id, {"status": "closed"})
        return original_modify(cart_id, change)

    monkeypatch.setattr(repo, "modify", close_before_modify)

    with pytest.raises(CartNotFoundError):
        cart_service.remove_item(
            customer_id=1,
            menu_item_id=1,
        )

    saved_cart = repo.get_by_id(1)
    assert saved_cart["status"] == "closed"
    assert saved_cart["items"] == [
        {"menu_item_id": 1, "quantity": 2}
    ]
    assert saved_cart["restaurant_id"] == 1


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


def test_clear_cart_removes_items_and_resets_totals(cart_service):
    """Test that clearing a cart removes items and resets totals."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cleared_cart = cart_service.clear_cart(customer_id=1)

    assert cleared_cart["items"] == []
    assert cleared_cart["restaurant_id"] is None
    assert cleared_cart["status"] == "active"

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart["items"] == []
    assert saved_cart["restaurant_id"] is None

    details = cart_service.get_cart_details(customer_id=1)
    assert details["items"] == []
    assert details["subtotal"] == 0
    assert details["total"] == 0
    assert details["problems"] == []


def test_clear_already_empty_cart(cart_service):
    """Test that clearing an already empty cart succeeds."""
    cart_service.clear_cart(customer_id=1)
    cleared_cart = cart_service.clear_cart(customer_id=1)

    assert cleared_cart["items"] == []
    assert cleared_cart["restaurant_id"] is None
    assert cleared_cart["status"] == "active"

    details = cart_service.get_cart_details(customer_id=1)
    assert details["subtotal"] == 0
    assert details["total"] == 0


def test_clear_cart_no_active_cart(cart_service):
    """Test that clearing a missing cart leaves existing data unchanged."""
    original_cart = cart_service.cart_repository.get_active_for_customer(1)

    with pytest.raises(CartNotFoundError):
        cart_service.clear_cart(customer_id=99)

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_clear_cart_only_own_cart(cart_service):
    """Test that a customer can't clear another customer's cart."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    original_cart = cart_service.cart_repository.get_active_for_customer(1)

    with pytest.raises(CartNotFoundError):
        cart_service.clear_cart(customer_id=2)

    saved_cart = cart_service.cart_repository.get_active_for_customer(1)
    assert saved_cart == original_cart


def test_clear_cart_invalid_saved_cart_unchanged(cart_service):
    """Test that invalid saved cart data is not modified."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cart_file = cart_service.cart_repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    with pytest.raises(ValidationError):
        cart_service.clear_cart(customer_id=1)

    assert cart_file.read_text() == original_data


def test_clear_cart_duplicate_items_unchanged(cart_service):
    """Test that duplicate cart items are not cleared."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    cart_file = cart_service.cart_repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"].append(
        {"menu_item_id": 1, "quantity": 3}
    )
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    with pytest.raises(ValueError, match="Duplicate cart items"):
        cart_service.clear_cart(customer_id=1)

    assert cart_file.read_text() == original_data


def test_clear_cart_closed_before_modify(cart_service, monkeypatch):
    """Test that a cart closed before modification is not cleared."""
    cart_service.add_item(
        customer_id=1,
        menu_item_id=1,
        quantity=2,
    )

    repository = cart_service.cart_repository
    original_cart = repository.get_active_for_customer(1)
    original_modify = repository.modify

    def closed_before_modify(cart_id, change):
        """Simulate check out closing the cart before modification."""
        repository.update(cart_id, {"status": "closed"})
        return original_modify(cart_id, change)

    monkeypatch.setattr(repository, "modify", closed_before_modify)

    with pytest.raises(CartNotFoundError):
        cart_service.clear_cart(customer_id=1)

    shopping = json.loads(repository.file_path.read_text())
    saved_cart = shopping["carts"][0]

    assert saved_cart["status"] == "closed"
    assert saved_cart["items"] == original_cart["items"]
    assert saved_cart["restaurant_id"] == original_cart["restaurant_id"]
