from pathlib import Path
from typing import Any

from app.repositories.json_store import (
    data_path,
    read_records,
    update_records,
)


class RestaurantMissingError(Exception):
    """The restaurant to update was not found."""


class RestaurantRepo:

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = (
            Path(file_path)
            if file_path is not None
            else data_path("restaurants.json")
        )

    def get_all(self) -> list[dict[str, Any]]:
        return read_records(self.file_path)

    def get_by_id(self, restaurant_id: int) -> dict[str, Any] | None: # searches the saved restaurants for a matching ID
        for restaurant in self.get_all():
            if restaurant["id"] == restaurant_id:
                return restaurant # returns restaurant details if found

        return None

    def create(self, name: str, cuisine: str, address: str) -> dict[str, Any]:
        def add_restaurant(records: list[dict]) -> dict[str, Any]:
            next_id = 1

            for restaurant in records: # Find the next available restaurant ID
                if restaurant["id"] >= next_id:
                    next_id = restaurant["id"] + 1

            new_restaurant = {
                "id": next_id,
                "name": name,
                "cuisine": cuisine,
                "address": address,
            }

            records.append(new_restaurant)
            return new_restaurant

        return update_records(self.file_path, add_restaurant)

    def update(self, restaurant_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        def change_restaurant(records: list[dict]) -> dict[str, Any]:
            for restaurant in records:
                if restaurant["id"] == restaurant_id:
                    for field, value in changes.items():
                        restaurant[field] = value

                    return restaurant

            raise RestaurantMissingError("Restaurant not found")

        return update_records(self.file_path, change_restaurant)