from typing import Any

import pytest

from app.services.restaurant_service import (
    RestaurantNotFoundError,
    RestaurantService,
)
from app.services.menu_service import MenuItemNotFoundError, MenuService


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
            "price": 800,
            "available": False,
        },
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Kebab Plate",
            "price": 1600,
            "available": True,
        },
        {
            "id": 2,
            "restaurant_id": 1,
            "name": "Fries",
            "price": 600,
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

    with pytest.raises(RestaurantNotFoundError):
        service.get_menu(999)

def make_menu_item_service() -> MenuService:
    restaurants = [{"id": 1}, {"id": 2}]
    menu_items = [
        {"id": 1, "restaurant_id": 1, "name": "Pizza", "price": 1600, "available": True},
        {"id": 2, "restaurant_id": 2, "name": "Tacos", "price": 1400, "available": False},
    ]

    class FakeMenuRepository:
        def get_by_id(self, item_id: int) -> dict[str, Any] | None:
            for item in menu_items:
                if item["id"] == item_id:
                    return item
            return None

    class FakeRestaurantRepository:
        def get_by_id(self, restaurant_id: int) -> dict[str, Any] | None:
            for restaurant in restaurants:
                if restaurant["id"] == restaurant_id:
                    return restaurant
            return None

    return MenuService(FakeMenuRepository(), FakeRestaurantRepository())

def test_get_menu_item() -> None:
    service = make_menu_item_service()

    assert service.get_menu_item(1, 1)["name"] == "Pizza"
    assert service.get_menu_item(2, 2)["available"] is False


def test_get_menu_item_unknown_restaurant() -> None:
    with pytest.raises(RestaurantNotFoundError):
        make_menu_item_service().get_menu_item(999, 1)


def test_get_menu_item_unknown_item() -> None:
    with pytest.raises(MenuItemNotFoundError):
        make_menu_item_service().get_menu_item(1, 999)


def test_get_menu_item_from_another_restaurant() -> None:
    # Item 2 exists, but it belongs to restaurant 2
    with pytest.raises(MenuItemNotFoundError):
        make_menu_item_service().get_menu_item(1, 2)

def test_add_menu_item_unknown_restaurant_raises():
    service = make_menu_item_service()
    with pytest.raises(RestaurantNotFoundError):
        service.add_menu_item(999, {"name": "X", "price": 100, "available": True})

def test_update_menu_item_from_another_restaurant_raises():
    service = make_menu_item_service()
    with pytest.raises(MenuItemNotFoundError):
        service.update_menu_item(1, 2, {"price": 500})