import json
from typing import Any


class MenuRepo:

    def __init__(self, file_path):
        self.file_path = file_path

    def get_all(self) -> list[dict[str, Any]]:
        with open(self.file_path, "r") as file:
            return json.load(file)

    def get_by_id(self, item_id: int) -> dict[str, Any] | None:
        for item in self.get_all():
            if item["id"] == item_id:
                return item

        return None

    def get_by_restaurant_id(
        self, restaurant_id: int
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in self.get_all()
            if item["restaurant_id"] == restaurant_id
        ]