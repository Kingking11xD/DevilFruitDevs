from typing import Any

import pytest

from app.services.restaurant_service import (
    RestaurantNotFoundError,
    RestaurantService,
)
from app.services.menu_service import MenuService

def test_get_restaurant_by_id() -> None:
    restaurant = {
        "id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"
    }

    class FakeRepository:
        def get_by_id(self, restaurant_id: int) -> dict[str, Any] | None:
            if restaurant_id == 1:
                return restaurant
            return None

    service = RestaurantService(FakeRepository())

    assert service.get_restaurant_by_id(1) == restaurant

    with pytest.raises(RestaurantNotFoundError):
        service.get_restaurant_by_id(999)

def test_get_menu() -> None:
    restaurants = [
        {
            "id": 1,
            "name": "Kebab",
            "cuisine": "Turkish",
            "address": "120 Lovely Rd",
        }
    ]

    menu_items = [
        {
            "id": 3,
            "restaurant_id": 1,
            "name": "Garlic Bread",
            "price": 7.99,
            "available": False,
        },
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Kebab Plate",
            "price": 15.99,
            "available": True,
        },
        {
            "id": 2,
            "restaurant_id": 1,
            "name": "Fries",
            "price": 5.99,
            "available": True,
        },
    ]

    class FakeMenuRepository:
        def get_by_restaurant_id(
            self, restaurant_id: int
        ) -> list[dict[str, Any]]:
            return [
                item
                for item in menu_items
                if item["restaurant_id"] == restaurant_id
            ]

    class FakeRestaurantRepository:
        def get_by_id(
            self, restaurant_id: int
        ) -> dict[str, Any] | None:
            for restaurant in restaurants:
                if restaurant["id"] == restaurant_id:
                    return restaurant
            return None

    service = MenuService(
        FakeMenuRepository(),
        FakeRestaurantRepository(),
    )

    result = service.get_menu(1)

    assert [item["id"] for item in result] == [1, 2, 3]
    assert result[2]["available"] is False