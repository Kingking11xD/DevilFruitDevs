import json
import pytest

from app.repositories.restaurant_repo import RestaurantRepo


def test_get_all_restaurants(tmp_path):
    expected = [
        {"id": 1, "name": "Kebab", "cuisine": "Turkish"},
        {"id": 2, "name": "Taco", "cuisine": "Mexican"},
        {"id": 3, "name": "Burger", "cuisine": "South Canada"}
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