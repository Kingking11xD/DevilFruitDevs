from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, read_shopping


class OrderRepo:
    """Read orders stored in shopping json file.
    Orders are only created during checkout, which saves the new order and
    closes the cart together in one write. repo only reads and doesnt write anything to the file on its own
    """

    def __init__(self, file_path: str | Path | None = None) -> None:
        """initialize the repo with the shopping file path."""
        self.file_path = (
            Path(file_path) if file_path is not None else data_path("shopping.json")
        )

    def get_all(self) -> list[dict[str, Any]]:
        """return all orders from the file"""
        shopping = read_shopping(self.file_path)
        return shopping["orders"]

    def get_by_id(self, order_id: int) -> dict[str, Any] | None:
        """Return order by ID, or None if not found."""
        for order in self.get_all():
            if order["id"] == order_id:
                return order

        return None

    def get_for_customer(self, customer_id: int) -> list[dict[str, Any]]:
        """return customer's orders, from newest to oldest"""
        orders = [
            order for order in self.get_all() if order["customer_id"] == customer_id
        ]
        return sorted(orders, key=lambda order: order["id"], reverse=True)

    def get_by_source_cart(self, cart_id: int) -> dict[str, Any] | None:
        """return order created from the cart, or None if none exists."""
        for order in self.get_all():
            if order["source_cart_id"] == cart_id:
                return order

        return None