import json
from pathlib import Path

import pytest

from app.repositories.restaurant_repo import RestaurantRepo
from app.repositories.menu_repo import MenuRepo


def test_get_all_restaurants(tmp_path):
    expected = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
        {"id": 3, "name": "Burger", "cuisine": "South Canada", "address": "20 Main St"}
    ]

    temp_path = tmp_path / "restaurants.json" 
    temp_path.write_text(json.dumps(expected), encoding="utf-8") 

    repository = RestaurantRepo(temp_path)
    result = repository.get_all() 

    assert result == expected # Does the loaded data match what we saved?


def test_invalid_json(tmp_path):
    temp_path = tmp_path / "invalid.json"
    temp_path.write_text("Large bags heavy bags danger cats", encoding="utf-8")
    #temp_path.write_text('[{"id": 1, "name": "Kebab", "cuisine": "Turkish"}]', encoding="utf-8") # A valid example

    repository = RestaurantRepo(temp_path)

    with pytest.raises(json.JSONDecodeError): # Temporarily check for and expect a JSON decode error
        repository.get_all()


def test_missing_file(tmp_path):
    repository = RestaurantRepo(tmp_path / "top-banana.json")
    # File is never written

    with pytest.raises(FileNotFoundError):
        repository.get_all()


def test_get_by_id(tmp_path: Path) -> None:
    data = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish", "address": "120 Lovely Rd"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican", "address": "213 Nowhere Ave"},
    ]
    file_path = tmp_path / "restaurants.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    repository = RestaurantRepo(file_path)

    assert repository.get_by_id(2) == data[1]
    assert repository.get_by_id(999) is None

def test_get_menu_by_restaurant_id(tmp_path: Path) -> None:
    data = [
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Margherita Pizza",
            "price": 15.99,
            "available": True,
        },
        {
            "id": 2,
            "restaurant_id": 2,
            "name": "Tacos al Pastor",
            "price": 13.99,
            "available": True,
        },
        {
            "id": 3,
            "restaurant_id": 1,
            "name": "Garlic Bread",
            "price": 7.99,
            "available": False,
        },
    ]

    file_path = tmp_path / "menu_items.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    repository = MenuRepo(file_path)

    result = repository.get_by_restaurant_id(1)

    assert result == [data[0], data[2]]