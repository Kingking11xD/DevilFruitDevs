import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from app.repositories.json_store import read_records, run_checkout_transaction

def write_json(path: Path, data) -> None:
    """Write JSON test data to a file."""
    path.write_text(json.dumps(data), encoding="utf-8")

@pytest.fixture
def files(tmp_path: Path) -> dict[str, Path]:
    """Create isolated shopping, account and menu files for each test."""
    shopping = tmp_path / "shopping.json"
    accounts = tmp_path / "accounts.json"
    menu_items = tmp_path / "menu_items.json"

    write_json(
        shopping,
        {
            "carts": [
                {
                    "id": 1,
                    "customer_id": 1,
                    "restaurant_id": 1,
                    "status": "active",
                    "items": [{"menu_item_id": 1, "quantity": 2}],
                }
            ],
            "orders": [],
        },
    )
    write_json(accounts, [{"id": 1, "name": "Ana", "active": True}])
    write_json(menu_items, [{"id": 1, "restaurant_id": 1, "price": 1250}])

    return {"shopping": shopping, "accounts": accounts, "menu_items": menu_items}


def place_order(shopping: dict, references: dict) -> dict:
    """Create an order from the active cart and close the cart, like checkout will."""
    cart = next(cart for cart in shopping["carts"] if cart["status"] == "active")
    price = references["menu_items"][0]["price"]
    order = {
        "id": len(shopping["orders"]) + 1,
        "source_cart_id": cart["id"],
        "total": price * cart["items"][0]["quantity"],
    }
    shopping["orders"].append(order)
    cart["status"] = "closed"
    return order


def references_for(files: dict[str, Path]) -> dict[str, Path]:
    """Return the reference files a checkout reads."""
    return {"accounts": files["accounts"], "menu_items": files["menu_items"]}


def test_checkout_saves_order_and_closes_cart_together(files: dict[str, Path]) -> None:
    """Test that the new order and the closed cart are saved in the same write."""
    order = run_checkout_transaction(files["shopping"], references_for(files), place_order)

    saved = json.loads(files["shopping"].read_text(encoding="utf-8"))
    assert saved["orders"] == [order]
    assert saved["carts"][0]["status"] == "closed"
    assert order["total"] == 2500


def test_checkout_receives_reference_data(files: dict[str, Path]) -> None:
    """Test that checkout can read accounts and menu items while the lock is held."""
    received = {}

    def capture(shopping: dict, references: dict) -> None:
        received.update(references)

    run_checkout_transaction(files["shopping"], references_for(files), capture)

    assert received["accounts"] == [{"id": 1, "name": "Ana", "active": True}]
    assert received["menu_items"] == [{"id": 1, "restaurant_id": 1, "price": 1250}]


def test_checkout_does_not_change_reference_files(files: dict[str, Path]) -> None:
    """Test that only the shopping file is saved, even if reference data is changed."""
    accounts_before = files["accounts"].read_bytes()
    menu_before = files["menu_items"].read_bytes()

    def change_references(shopping: dict, references: dict) -> None:
        references["accounts"][0]["active"] = False
        references["menu_items"][0]["price"] = 1

    run_checkout_transaction(files["shopping"], references_for(files), change_references)

    assert files["accounts"].read_bytes() == accounts_before
    assert files["menu_items"].read_bytes() == menu_before


def test_failed_validation_keeps_previous_state(files: dict[str, Path]) -> None:
    """Test that an error during checkout leaves the cart and orders unchanged."""
    before = files["shopping"].read_bytes()

    def reject_after_changes(shopping: dict, references: dict) -> None:
        place_order(shopping, references)
        raise ValueError("Menu item is unavailable")

    with pytest.raises(ValueError):
        run_checkout_transaction(files["shopping"], references_for(files), reject_after_changes)

    assert files["shopping"].read_bytes() == before


def test_failed_save_keeps_previous_state(files: dict[str, Path], tmp_path: Path) -> None:
    """Test that a save failure leaves the cart and orders unchanged and no temp file."""
    before = files["shopping"].read_bytes()

    def add_unsaveable_order(shopping: dict, references: dict) -> None:
        shopping["carts"][0]["status"] = "closed"
        shopping["orders"].append({"id": object()})  # Cannot be written as JSON

    with pytest.raises(TypeError):
        run_checkout_transaction(files["shopping"], references_for(files), add_unsaveable_order)

    assert files["shopping"].read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "accounts.json",
        "menu_items.json",
        "shopping.json",
    ]


def test_missing_reference_file_keeps_previous_state(files: dict[str, Path], tmp_path: Path) -> None:
    """Test that a missing reference file stops checkout before anything is saved."""
    before = files["shopping"].read_bytes()
    references = {"accounts": files["accounts"], "menu_items": tmp_path / "missing.json"}

    with pytest.raises(FileNotFoundError):
        run_checkout_transaction(files["shopping"], references, place_order)

    assert files["shopping"].read_bytes() == before


def test_checkout_releases_lock(files: dict[str, Path]) -> None:
    """Test that other storage reads still work after a checkout, including a failed one."""
    run_checkout_transaction(files["shopping"], references_for(files), place_order)

    def fail(shopping: dict, references: dict) -> None:
        raise ValueError("Cart is empty")

    with pytest.raises(ValueError):
        run_checkout_transaction(files["shopping"], references_for(files), fail)

    with ThreadPoolExecutor(max_workers=1) as worker:
        accounts = worker.submit(read_records, files["accounts"]).result(timeout=2)

    assert accounts[0]["id"] == 1


def test_concurrent_checkouts_create_one_order(files: dict[str, Path]) -> None:
    """Test that two checkouts of the same cart at the same time create only one order."""

    def checkout_if_active(shopping: dict, references: dict) -> dict | None:
        if not any(cart["status"] == "active" for cart in shopping["carts"]):
            return None
        return place_order(shopping, references)

    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [
            workers.submit(
                run_checkout_transaction,
                files["shopping"],
                references_for(files),
                checkout_if_active,
            )
            for _ in range(2)
        ]
        results = [future.result(timeout=5) for future in futures]

    saved = json.loads(files["shopping"].read_text(encoding="utf-8"))
    assert len(saved["orders"]) == 1
    assert sorted(result is None for result in results) == [False, True]