from app.services.pricing import price_items

MENU = {
    1: {"id": 1, "restaurant_id": 1, "name": "Burger", "price": 1250, "available": True},
    2: {"id": 2, "restaurant_id": 1, "name": "Fries", "price": 400, "available": True},
}

def test_price_items_multiple_lines() -> None:
    """Test line totals, subtotal and total for several items and quantities."""
    result = price_items(
        [{"menu_item_id": 1, "quantity": 2}, {"menu_item_id": 2, "quantity": 3}], MENU)

    assert [line["line_total"] for line in result["items"]] == [2500, 1200]
    assert result["items"][0]["name"] == "Burger"
    assert result["items"][0]["unit_price"] == 1250
    assert result["subtotal"] == 3700
    assert result["total"] == 3700


def test_price_items_empty_cart() -> None:
    """Test that an empty cart costs nothing."""
    assert price_items([], MENU) == {"items": [], "subtotal": 0, "total": 0}