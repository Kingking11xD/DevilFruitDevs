from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, read_records

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