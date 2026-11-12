import json
import os
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_storage_lock = Lock() # All JSON reads and updates take turns using this lock


def data_path(filename: str) -> Path:
    folder = Path(os.environ.get("DATA_DIR", "data"))
    if not folder.is_absolute():
        folder = PROJECT_ROOT / folder
    return folder / filename


def _read(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected a JSON list of records")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a JSON object")

    return records

def _read_shopping(path: Path) -> dict[str, list[dict]]:
    """Read and validates the shared shopping JSON file."""
    with path.open("r", encoding="utf-8") as file:
        shopping = json.load(file)

    if not isinstance(shopping, dict):
        raise ValueError("Expected a JSON shopping object")

    if set(shopping) != {"carts", "orders"}:
        raise ValueError("Expected carts and orders in shopping data")

    for records in shopping.values():
        if not isinstance(records, list):
            raise ValueError("Expected a JSON list of records")

        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each record must be a JSON object")

    return shopping


def _save(
        path: Path, records: list[dict] | dict[str, list[dict]]
) -> None:
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.write("\n")

        os.replace(temporary_path, path) # Close the temp file before replacing the original
    finally:
        if temporary_path is not None: # Remove the temp file if saving failed
            temporary_path.unlink(missing_ok=True)


def read_records(path: str | Path) -> list[dict]:
    path = Path(path).resolve()
    with _storage_lock:
        return _read(path)

def read_shopping(path: str | Path) -> dict[str, list[dict]]:
    """Safely read and return the shopping cart and order data."""
    path = Path(path).resolve()

    with _storage_lock:
        return _read_shopping(path)

def update_records(
    path: str | Path,
    change: Callable[[list[dict]], Any],
) -> Any:
    """Run a repository's change function and save before returning its result."""
    path = Path(path).resolve()

    with _storage_lock:
        records = _read(path)
        result = change(records) # The repository changes this list while the storage lock is held
        _save(path, records)
        return result

def update_shopping(
        path: str | Path,
        change: Callable[[dict[str, list[dict]]], Any],
) -> Any:
    """Safely update and save shopping cart and order data."""
    path = Path(path).resolve()

    with _storage_lock:
        shopping = _read_shopping(path)
        result = change(shopping)
        _save(path, shopping)
        return result


def run_checkout_transaction(
        shopping_path: str | Path,
        reference_paths: Mapping[str, str | Path],
        change: Callable[[dict[str, list[dict]], dict[str, list[dict]]], Any],
) -> Any:
    """Read related data, run a checkout change and save shopping data atomically.
 
    The shared lock is held from the first read until the save, so no other
    request can change the cart, menu or account while checkout validates it.
 
    ``reference_paths`` names the list files checkout needs to read, such as
    accounts, restaurants and menu items. They are read without taking the
    lock again and are never saved.
 
    ``change`` receives the shopping data and the reference data. It may add
    an order and close the cart in the shopping data. It must not call
    ``read_records``, ``read_shopping`` or any repository method, because the
    lock is already held. If ``change`` raises an error, nothing is saved.
    """
    shopping_path = Path(shopping_path).resolve()
    resolved_paths = {name: Path(path).resolve() for name, path in reference_paths.items()}
 
    with _storage_lock:
        references = {name: _read(path) for name, path in resolved_paths.items()}
        shopping = _read_shopping(shopping_path)
        result = change(shopping, references)
        _save(shopping_path, shopping)  # Order and closed cart are written in one replacement
        return result
 