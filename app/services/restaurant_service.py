from app.repositories.restaurant_repo import RestaurantRepo
from typing import Any

class RestaurantNotFoundError(Exception):
    """The requested restaurant does not exist."""

class RestaurantService:

    def __init__(self, repository: RestaurantRepo) -> None:
        self.repository = repository

    def get_all_restaurants(
            self, search: str | None = None
    ) -> list[dict[str, Any]]:
        """Return all restaurants that match the optional name search"""
        restaurants = self.repository.get_all()

        if search is None or not search.strip():
            return restaurants
        
        search_term = search.strip().casefold()

        return [
            restaurant for restaurant in restaurants
            if search_term in restaurant["name"].casefold()
        ]

    def get_restaurant_by_id(self, restaurant_id: int) -> dict[str, Any]:
        restaurant = self.repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError("Restaurant not found")

        return restaurant