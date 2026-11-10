"""API routes for shopping carts"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_current_customer
from app.repositories.cart_repo import CartRepo
from app.schemas.cart import Cart

router = APIRouter()
repository = CartRepo()

@router.post(
    "/customers/me/cart",
    response_model=Cart,
    status_code=201,
    summary="Create or retrieve active cart",
    description=(
        "Create an active cart for the signed in customer, or return "
        "their existing active cart without creating a duplicate."
    ),
    responses={
        200: {"description": "Existing active cart returned"},
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def create_cart(
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
    response: Response,
) -> Cart:
    """Create a cart or return the customer's existing active cart."""
    try:
        cart, created = repository.create(account["id"])
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error
    
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return Cart.model_validate(cart)

@router.get(
    "/customers/me/cart",
    response_model=Cart,
    summary="Get active cart",
    description=(
        "Retrieve the signed in customer's active cart."
        "This endpoint doesn't create a new cart."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        404: {"description": "Active cart not found"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def get_cart(
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> Cart:
    """Return the customer's active cart without creating one."""
    try:
        cart = repository.get_active_for_customer(account["id"])
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error
    
    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Active cart not found",
        )
    
    return Cart.model_validate(cart)