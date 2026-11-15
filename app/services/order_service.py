from typing import Any
from app.repositories.order_repo import OrderRepo

class OrderNotFoundError(Exception):
    """Raised when an order doesn't exist or belongs to another customer."""


class OrderService:
    """Retrieve orders for the signed-in customer."""

    def __init__(self, repository: OrderRepo) -> None:
        """Initialize the service with an order repository."""
        self.repository = repository

    def list_for_customer(self, customer_id: int) -> list[dict[str, Any]]:
        """Return a customer's orders, newest first."""
        return self.repository.get_for_customer(customer_id)

    def get_for_customer(self, customer_id: int, order_id: int) -> dict[str, Any]:
        """Return one of a customer's orders.
        Another customer's order is treated the same as a missing order, so
        the response doesn't reveal which order IDs exist.
        """
        order = self.repository.get_by_id(order_id)
        if order is None or order["customer_id"] != customer_id:
            raise OrderNotFoundError(order_id)
        return order