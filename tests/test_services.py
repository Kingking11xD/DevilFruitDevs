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
