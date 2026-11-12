from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, run_checkout_transaction
from app.schemas.order import Order
from app.services.pricing import price_items


class CheckoutError(Exception):
    """Base class for reasons a checkout is rejected."""


class InactiveCustomerError(CheckoutError):
    """The customer doesn't exist or has been deactivated."""


class MissingAddressError(CheckoutError):
    """The customer has no delivery address."""


class NoActiveCartError(CheckoutError):
    """The customer has no active cart."""


class EmptyCartError(CheckoutError):
    """The active cart has no items."""


class UnavailableItemError(CheckoutError):
    """The restaurant or a menu item is missing, unavailable or doesn't match the cart."""

class TotalChangedError(CheckoutError):
    """The current total differs from the total the customer confirmed."""
    def __init__(self, total: int) -> None:
        super().__init__(total)
        self.total = total

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _find(records: list[dict[str, Any]], record_id: Any) -> dict[str, Any] | None:
    return next((record for record in records if record["id"] == record_id), None)


class CheckoutService:
    """Turn a customer's active cart into a saved order."""

    def __init__(
            self,
            shopping_path: str | Path | None = None,
            accounts_path: str | Path | None = None,
            restaurants_path: str | Path | None = None,
            menu_items_path: str | Path | None = None,
            clock: Callable[[], str] = _utc_now) -> None:
        self.shopping_path = shopping_path or data_path("shopping.json")
        self.reference_paths = {
            "accounts": accounts_path or data_path("accounts.json"),
            "restaurants": restaurants_path or data_path("restaurants.json"),
            "menu_items": menu_items_path or data_path("menu_items.json"),
        }
        self.clock = clock

    def checkout(self, customer_id: int, expected_total: int) -> dict[str, Any]:
        """Validate the customer's active cart, save it as an order and close the cart.
        If any check fails, nothing is saved."""

        def place_order(shopping: dict[str, list[dict]], references: dict[str, list[dict]]) -> dict[str, Any]:
            customer = _find(references["accounts"], customer_id)
            if customer is None or not customer.get("active", False):
                raise InactiveCustomerError(customer_id)
            if not customer.get("delivery_address"):
                raise MissingAddressError(customer_id)

            cart = next(
                (cart for cart in shopping["carts"]
                 if cart["customer_id"] == customer_id and cart["status"] == "active"),
                None,
            )
            if cart is None:
                raise NoActiveCartError(customer_id)
            if not cart["items"]:
                raise EmptyCartError(cart["id"])

            restaurant = _find(references["restaurants"], cart["restaurant_id"])
            if restaurant is None:
                raise UnavailableItemError("Restaurant no longer exists")

            menu_items = {item["id"]: item for item in references["menu_items"]}
            for cart_item in cart["items"]:
                menu_item = menu_items.get(cart_item["menu_item_id"])
                if (
                    menu_item is None
                    or menu_item["restaurant_id"] != restaurant["id"]
                    or not menu_item.get("available", False)
                    or not menu_item.get("active", True)  # Same rule as adding to the cart
                ):
                    raise UnavailableItemError(cart_item["menu_item_id"])

            prices = price_items(cart["items"], menu_items)
            if prices["total"] != expected_total:
                raise TotalChangedError(prices["total"])  # Customer must review the new total
            order = {
                "id": max((order["id"] for order in shopping["orders"]), default=0) + 1,
                "customer_id": customer_id,
                "customer_name": customer["name"],
                "restaurant_id": restaurant["id"],
                "restaurant_name": restaurant["name"],
                "source_cart_id": cart["id"],
                "status": "placed",
                "created_at": self.clock(),
                "delivery_address": customer["delivery_address"],
                **prices,
            }
            Order.model_validate(order) #order that breaks the order rules is never saved

            shopping["orders"].append(order)
            cart["status"] = "closed"  # saved in the same write as the order
            return order

        return run_checkout_transaction(self.shopping_path, self.reference_paths, place_order)