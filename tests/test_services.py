from typing import Any

import pytest

from app.services.restaurant_service import (
    RestaurantNotFoundError,
    RestaurantService,
)


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


def test_create_restaurant(): # Test that the service passes restaurant details to the repository and returns the result
    class FakeRepository: # A fake repository keeps this test from using real files
        def create(self, name, cuisine, address):
            return {
                "id": 1,
                "name": name,
                "cuisine": cuisine,
                "address": address,
            }

    service = RestaurantService(FakeRepository())

    result = service.create_restaurant(
        "Baratie", "Seafood", "East Blue"
    )

    assert result == {
        "id": 1,
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    }
