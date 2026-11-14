"""API routes for shopping carts"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status, Path

from app.api.dependencies import get_current_customer
from app.repositories.cart_repo import CartRepo
from app. repositories.menu_repo import MenuRepo
from app.schemas.cart import Cart, CartItemAdd, CartItemUpdate, CartDetail
from app.services.cart_service import (
    CartNotFoundError,
    CartItemNotFoundError,
    CartRestaurantMismatchError,
    CartService,
    MenuItemNotAvailableError,
)
from app.services.menu_service import MenuItemNotFoundError

router = APIRouter()
repository = CartRepo()
menu_repository = MenuRepo()
service = CartService(repository, menu_repository)


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
        validated_cart = Cart.model_validate(cart)
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error

    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return validated_cart


@router.get(
    "/customers/me/cart",
    response_model=CartDetail,
    summary="View my cart and total",
    description=(
        "Get the authenticated customer's active cart with current "
        "menu item prices, quantities, line totals, subtotal, total, "
        "and item problems."
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
) -> CartDetail:
    """Return the customer's active cart with calculated totals."""
    try:
        cart = service.get_cart_details(account["id"])
        return CartDetail.model_validate(cart)

    except CartNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Active cart not found",
        ) from error

    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error


@router.post(
    "/customers/me/cart/items",
    response_model=Cart,
    status_code=200,
    summary="Add an item to my cart",
    description=(
        "Add an available menu item to the signed in customer's active cart."
        "If the item is already in the cart, increase its quantity."
        "Items must belong to the same restaurant."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        404: {"description": "Cart or menu item not found"},
        409: {"description": "Item unavailable or restaurant mismatch"},
        422: {"description": "Invalid item ID or quantity"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def add_cart_item(
    item: CartItemAdd,
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> Cart:
    """Add a menu item to the customer's active cart."""
    try:
        cart = service.add_item(
            customer_id=account["id"],
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
        )
        validated_cart = Cart.model_validate(cart)

    except (CartNotFoundError, MenuItemNotFoundError) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        MenuItemNotAvailableError,
        CartRestaurantMismatchError,
    ) as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error

    return validated_cart


@router.patch(
    "/customers/me/cart/items/{item_id}",
    response_model=CartDetail,
    status_code=200,
    summary="Update item quantity in my cart",
    description=(
        "Replace the quantity of an existing item in the signed in "
        "customer's active cart and return the updated cart with totals."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        404: {"description": "Cart or cart item not found"},
        422: {"description": "Invalid item ID or quantity"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def update_cart_item_quantity(
    item_id: Annotated[
        int,
        Path(gt=0, description="Menu item ID of the item in the cart"),
    ],
    item: CartItemUpdate,
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> CartDetail:
    """Update an existing cart item's quantity and return updated totals."""
    try:
        service.update_item_quantity(
            customer_id=account["id"],
            menu_item_id=item_id,
            quantity=item.quantity,
        )
        cart = service.get_cart_details(account["id"])
        return CartDetail.model_validate(cart)

    except (CartNotFoundError, CartItemNotFoundError) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error


@router.delete(
    "/customers/me/cart/items/{item_id}",
    status_code=204,
    summary="Remove an item from my cart",
    description=(
        "Remove an existing menu item from the signed in customer's  active cart."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        404: {"description": "Cart or cart item not found"},
        422: {"description": "Invalid item ID"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def remove_cart_item(
    item_id: Annotated[
        int,
        Path(gt=0, description="Menu item ID of the item in the cart"),
    ],
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> None:
    """Remove an existing item from the customer's active cart."""
    try:
        service.remove_item(
            customer_id=account["id"],
            menu_item_id=item_id,
        )

    except (CartNotFoundError, CartItemNotFoundError) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error


@router.delete(
    "/customers/me/cart/items",
    status_code=204,
    summary="Clear my cart",
    description=(
        "Remove all items from the signed in customer's active cart "
        "and reset its restaurant. Clearing an empty cart also succeeds."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is inactive or unauthorized"},
        404: {"description": "Active cart not found"},
        500: {"description": "Cart storage is unavailable"},
    },
)
def clear_cart(
    account: Annotated[dict[str, Any], Depends(get_current_customer)],
) -> None:
    """Remove all items from the customer's active cart."""
    try:
        service.clear_cart(customer_id=account["id"])

    except CartNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (OSError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=500,
            detail="Cart storage is unavailable",
        ) from error
