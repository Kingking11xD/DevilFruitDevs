from app.repositories.restaurant_repo import RestaurantRepo
from typing import Any

class RestaurantNotFoundError(Exception):
    """The requested restaurant does not exist."""

class RestaurantService:

    def __init__(self, repository: RestaurantRepo) -> None:
        self.repository = repository

    def get_all_restaurants(
            self,
            search: str | None = None,
            cuisine: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return all restaurants that match the optional search and cuisine filters"""
        restaurants = self.repository.get_all()
        
        search_term = search.strip().casefold() if search else ""
        cuisine_term = cuisine.strip().casefold() if cuisine else ""

        if search_term:
            restaurants = [
                restaurant for restaurant in restaurants
                if search_term in restaurant["name"].casefold()
            ]

        if cuisine_term:
            restaurants = [
                restaurant for restaurant in restaurants
                if restaurant["cuisine"].strip().casefold() == cuisine_term
            ]

        return restaurants

    def get_restaurant_by_id(self, restaurant_id: int) -> dict[str, Any]:
        restaurant = self.repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError("Restaurant not found")

        return restaurant