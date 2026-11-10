"""API routes for shopping carts"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_current_customer
from app.repositories.cart_repo import CartRepo
from app.schemas.cart import Cart

router = APIRouter()
repository = CartRepo()

@router.post("/customers/me/cart", response_model=Cart)
def create_cart(
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
    response: Response,
) -> Cart:
    """Create a cart or return the customer's existing active cart."""
    try:
        cart, created = repository.create(account["id"])
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        )
    
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return Cart.model_validate(cart)

@router.get("/customers/me/cart", response_model=Cart)
def get_cart(
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> Cart:
    """Return the customer's active cart without creating one."""
    try:
        cart = repository.get_active_for_customer(account["id"])
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        )
    
    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Active cart not found",
        )
    
    return Cart.model_validate(cart)