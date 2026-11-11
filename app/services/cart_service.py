from typing import Any

from app.services.menu_service import MenuItemNotFoundError
from app.repositories.cart_repo import CartRepo
from app.repositories.menu_repo import MenuRepo


class CartNotFoundError(Exception):
    """Raised when the customer has no active cart."""


class MenuItemNotAvailableError(Exception):
    """Raised when a menu item is unavailable or inactive."""


class CartRestaurantMismatchError(Exception):
    """Raised when an item belongs to a different restaurant."""


class CartService:
    """Handle shopping cart operations."""
    def __init__(
            self,
            cart_repository: CartRepo,
            menu_repository: MenuRepo,
    ) -> None:
        """Initialize the cart service with its repository"""
        self.cart_repository = cart_repository
        self.menu_repository = menu_repository

    def add_item(
            self,
            customer_id: int,
            menu_item_id: int,
            quantity: int,
    ) -> dict[str, Any]:
        """Add a menu item to the customer's active cart."""
        menu_item = self.menu_repository.get_by_id(menu_item_id)

        if menu_item is None:
            raise MenuItemNotFoundError("Menu item not found")

        if not menu_item["available"] or not menu_item.get("active", True):
            raise MenuItemNotAvailableError("Menu item is unavailable")

        cart = self.cart_repository.get_active_for_customer(customer_id)

        if cart is None:
            raise CartNotFoundError("Active cart not found")

        def change(current_cart: dict[str, Any]) -> None:
            """Add the item to the latest saved cart."""
            if (
                current_cart["status"] != "active"
                or current_cart["customer_id"] != customer_id
            ):
                raise CartNotFoundError("Active cart not found")

            restaurant_id = menu_item["restaurant_id"]

            if (
                current_cart["restaurant_id"] is not None
                and current_cart["restaurant_id"] != restaurant_id
            ):
                raise CartRestaurantMismatchError(
                    "Can't add items from different restaurants"
                )

            current_cart["restaurant_id"] = restaurant_id

            for item in current_cart["items"]:
                if item["menu_item_id"] == menu_item_id:
                    item["quantity"] += quantity
                    return

            current_cart["items"].append({
                "menu_item_id": menu_item_id,
                "quantity": quantity,
            })

        updated_cart = self.cart_repository.modify(cart["id"], change)

        if updated_cart is None:
            raise CartNotFoundError("Active cart not found")

        return updated_cart
