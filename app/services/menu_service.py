from typing import Any

from app.repositories.menu_repo import MenuRepo
from app.repositories.restaurant_repo import RestaurantRepo
from app.services.restaurant_service import RestaurantNotFoundError

class MenuItemNotFoundError(Exception):
    """The requested menu item does not exist for that restaurant."""

class MenuService:
    def __init__(
        self,
        menu_repository: MenuRepo,
        restaurant_repository: RestaurantRepo,
    ) -> None:
        self.menu_repository = menu_repository
        self.restaurant_repository = restaurant_repository

    def get_menu(
        self, restaurant_id: int
    ) -> list[dict[str, Any]]:

        restaurant = self.restaurant_repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError("Restaurant not found")

        items = self.menu_repository.get_by_restaurant_id(
            restaurant_id
        )

        return sorted(items, key=lambda item: item["id"])

    def get_menu_item(
        self, restaurant_id: int, item_id: int
    ) -> dict[str, Any]:

        restaurant = self.restaurant_repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError("Restaurant not found")

        item = self.menu_repository.get_by_id(item_id)

        # An item that belongs to another restaurant counts as not found
        if item is None or item["restaurant_id"] != restaurant_id:
            raise MenuItemNotFoundError("Menu item not found")

        return item