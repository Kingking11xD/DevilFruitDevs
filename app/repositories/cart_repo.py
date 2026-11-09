from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, read_shopping, update_shopping

class CartRepo:
    """Manage shopping carts stored in the shared shopping JSON file."""
    def __init__(self, file_path: str | Path | None = None) -> None:
        """Initialize the repository with the shopping file path."""
        self.file_path = (
            Path(file_path) if file_path is not None else data_path("shopping.json")
        )

    def get_all(self) -> list[dict[str, Any]]:
        """Return all shopping carts from the shared shopping file."""
        shopping = read_shopping(self.file_path)
        return shopping["carts"]
    
    def get_by_id(self, cart_id: int) -> dict[str, Any] | None:
        """Return a shopping cart by its ID, or None if not found."""
        for cart in self.get_all():
            if cart["id"] == cart_id:
                return cart
            
        return None
    
    def get_active_for_customer(
            self, customer_id: int
    ) -> dict[str, Any] | None:
        """Return a customer's active cart, or None if none exists."""
        for cart in self.get_all():
            if cart["customer_id"] == customer_id and cart["status"] == "active":
                return cart
            
        return None
    
    def create(self, customer_id: int) -> tuple[dict[str, Any], bool]:
        """Return the customer's active cart and whether it was newly created."""
        def add(shopping: dict[str, Any]) -> tuple[dict[str, Any], bool]:
            """Find an existing active cart or create a new one."""
            carts = shopping["carts"]

            for cart in carts:
                if cart["customer_id"] == customer_id and cart["status"] == "active":
                    return cart, False
                
            new_id = max((cart["id"] for cart in carts), default=0) + 1

            cart = {
                "id": new_id,
                "customer_id": customer_id,
                "restaurant_id": None,
                "status": "active",
                "items": [],
            }

            carts.append(cart)
            return cart, True
        
        return update_shopping(self.file_path, add)
    
    def update(
            self, cart_id: int, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update an existing shopping cart and return it, or None if not found."""
        allowed_fields = {"restaurant_id", "status", "items"}

        if not set(changes).issubset(allowed_fields):
            raise ValueError("Can't update protected cart fields")

        def apply(shopping: dict[str, Any]) -> dict[str, Any] | None:
            """Apply the supplied changes to the matching cart."""
            for cart in shopping["carts"]:
                if cart["id"] == cart_id:
                    cart.update(changes)
                    return cart
                
            return None
        
        return update_shopping(self.file_path, apply)