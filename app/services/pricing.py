from collections.abc import Mapping
from typing import Any


def price_items(
        cart_items: list[dict[str, Any]],
        menu_items: Mapping[int, dict[str, Any]]) -> dict[str, Any]:
    """Return each line's price snapshot plus the subtotal and total."""
    lines = []
    for cart_item in cart_items:
        menu_item = menu_items[cart_item["menu_item_id"]]
        quantity = cart_item["quantity"]
        lines.append({
            "menu_item_id": menu_item["id"],
            "name": menu_item["name"],
            "unit_price": menu_item["price"],
            "quantity": quantity,
            "line_total": menu_item["price"] * quantity,
        })

    subtotal = sum(line["line_total"] for line in lines)
    # tax and delivery fees are set for M3, so the total equals the subtotal for now.
    return {"items": lines, "subtotal": subtotal, "total": subtotal}