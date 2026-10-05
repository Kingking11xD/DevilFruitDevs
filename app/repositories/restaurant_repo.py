import json
from typing import Any

class RestaurantRepo:

    def __init__(self, file_path):
        self.file_path = file_path

    def get_all(self):
        with open(self.file_path, "r") as file:
            return json.load(file)

    def get_by_id(self, restaurant_id: int) -> dict[str, Any] | None: # searches the saved restaurants for a matching ID
        for restaurant in self.get_all():
            if restaurant["id"] == restaurant_id:
                return restaurant # returns restaurant details if found

        return None