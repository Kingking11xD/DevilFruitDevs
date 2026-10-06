import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep

import pytest

from app.repositories.json_store import data_path, read_records, update_records
from app.repositories.restaurant_repo import RestaurantRepo


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


def test_save_records(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text('[{"id": 1}]', encoding="utf-8")  # Start with one saved record

    def add_restaurant(records: list[dict]) -> None:
        records.append({"id": 2})

    update_records(path, add_restaurant)  # Add and save the new record

    assert read_records(path) == [{"id": 1}, {"id": 2}]  # Both records are still there


def test_invalid_structure(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text("{}", encoding="utf-8")  # Valid json but not a list

    with pytest.raises(ValueError):
        read_records(path)


def test_failed_save_keeps_data(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text('[{"id": 1}]', encoding="utf-8")
    before = path.read_bytes()  # Keep the original contents to compare

    def add_invalid_record(records: list[dict]) -> None:
        records.append({"value": object()})  # cannot be saved as json

    with pytest.raises(TypeError):
        update_records(path, add_invalid_record)

    assert path.read_bytes() == before  # Original data unchanged
    assert list(tmp_path.iterdir()) == [path]  # No temporary file left


def test_concurrent_updates(tmp_path: Path) -> None:
    path = tmp_path / "restaurants.json"
    path.write_text("[]", encoding="utf-8")

    def add_restaurant(number: int) -> None:
        def change(records: list[dict]) -> None:
            sleep(0.01)  # Give other updates time to overlap
            records.append({"id": number})

        update_records(path, change)

    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(add_restaurant, [1, 2]))  # Run both updates

    records = read_records(path)
    assert sorted(record["id"] for record in records) == [1, 2]  # Neither update was lost


def test_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    assert data_path("restaurants.json") == tmp_path / "restaurants.json"
