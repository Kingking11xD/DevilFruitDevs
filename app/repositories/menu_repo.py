from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, read_records


class MenuRepo:

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = (
            Path(file_path) if file_path is not None else data_path("menu_items.json")
        )

    def get_all(self) -> list[dict[str, Any]]:
        return read_records(self.file_path)

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