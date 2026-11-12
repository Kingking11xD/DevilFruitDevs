import json
from pathlib import Path
from app.repositories.order_repo import OrderRepo

def make_order(order_id: int, customer_id: int, source_cart_id: int, created_at: str = "2026-11-15T18:00:00Z",) -> dict:
    """Return a valid order record for tests."""
    return {
        "id": order_id,
        "customer_id": "Test Customer",
        "restaurant_id": 1,
        "restaurant_name": "Test Restaurant",
        "source_cart_id": source_cart_id,
        "status": "placed",
        "created_at": created_at,
        "delivery_address": "123 Test St",
        "items": [
            {
                "menu_item_id": 1,
                "name": "Burger",
                "unit_price": 1250,
                "quantity": 2,
                "line_total": 2500,
            }
        ],
        "subtotal": 2500,
        "total": 2500,
    }


def write_shopping(path: Path, carts: list | None = None, orders: list | None = None) -> None:
    """Write a shopping file with the given carts and orders."""
    path.write_text(
        json.dumps({"carts": carts or [], "orders": orders or []}),
        encoding="utf-8",
    )

def test_order_repo_get_by_id(tmp_path: Path) -> None:
    """Test retrieving an order by ID and handling a missing order."""
    path = tmp_path / "shopping.json"
    orders = [make_order(1, 1, 1), make_order(2, 2, 2)]
    write_shopping(path, orders=orders)
    repo = OrderRepo(path)

    assert repo.get_by_id(2) == orders[1]
    assert repo.get_by_id(999) is None

def test_order_repo_get_for_customer_newest_first(tmp_path: Path) -> None:
    """Test that only a customer's orders are returned, newest first."""
    path = tmp_path / "shopping.json"
    orders = [make_order(1, 1, 1), make_order(2, 2, 2), make_order(3, 1, 3)]
    write_shopping(path, orders=orders)
    repo = OrderRepo(path)

    result = repo.get_for_customer(1)

    assert [order["id"] for order in result] == [3, 1]
    assert all(order["customer_id"] == 1 for order in result)

 
def test_order_repo_get_for_customer_no_orders(tmp_path: Path) -> None:
    """Test that a customer with no orders gets an empty list."""
    path = tmp_path / "shopping.json"
    write_shopping(path, orders=[make_order(1, 1, 1)])

    assert OrderRepo(path).get_for_customer(2) == []


def test_order_repo_get_by_source_cart(tmp_path: Path) -> None:
    """Test finding the order created from a cart."""
    path = tmp_path / "shopping.json"
    orders = [make_order(1, 1, 5), make_order(2, 2, 6)]
    write_shopping(path, orders=orders)
    repo = OrderRepo(path)

    assert repo.get_by_source_cart(6) == orders[1]
    assert repo.get_by_source_cart(999) is None

def test_order_repo_does_not_change_file(tmp_path: Path) -> None:
    """Test that reading orders leaves the shopping file unchanged."""
    path = tmp_path / "shopping.json"
    write_shopping(path, orders=[make_order(1, 1, 1)])
    before = path.read_bytes()
    repo = OrderRepo(path)

    repo.get_all()
    repo.get_by_id(1)
    repo.get_for_customer(1)
    repo.get_by_source_cart(1)

    assert path.read_bytes() == before