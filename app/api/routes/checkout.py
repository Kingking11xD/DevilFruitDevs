from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Response

from app.api.dependencies import get_current_customer
from app.schemas.order import CheckoutRequest, Order
from app.services.checkout_service import (
    CartClosedError, CartNotFoundError, CheckoutService, EmptyCartError, InactiveCustomerError, 
    MissingAddressError, TotalChangedError, UnavailableItemError)

router = APIRouter()

def get_checkout_service() -> CheckoutService:
    """Create the checkout service. Tests replace this with isolated data."""
    return CheckoutService()


@router.post(
    "/carts/{cart_id}/checkout",
    response_model=Order,
    status_code=201,
    summary="Check out my cart",
    description="Turn the signed-in customer's active cart into a saved order. "
    "Send the total the customer saw in their cart as expected_total. "
    "Prices and availability are rechecked against current menu data; if the total "
    "has changed, nothing is saved so the customer can review their cart. "
    "The cart is closed only once the order is saved.",
    responses={
        200: {"model": Order, "description": "Cart was already checked out; the existing order is returned"},
        400: {"description": "Cart is empty or no delivery address is set"},
        401: {"description": "Authentication required or invalid"},
        403: {"description": "Account is inactive or is not a customer account"},
        404: {"description": "Cart not found (or it belongs to another customer)"},
        409: {"description": "A menu item or the restaurant is no longer available, the total has "
              "changed (the response includes the new total), or the cart is closed"},
        500: {"description": "Order could not be saved"},
    },
)
def checkout(
        cart_id: Annotated[int, Path(gt=0)],
        data: CheckoutRequest,
        response: Response,
        account: Annotated[dict[str, Any], Depends(get_current_customer)],
        service: Annotated[CheckoutService, Depends(get_checkout_service)]) -> dict[str, Any]:
    try:
        order, created = service.checkout(account["id"], cart_id, data.expected_total)
        if not created:
            response.status_code = 200  # Retry: same order, nothing new created
        return order
    except InactiveCustomerError as error:
        raise HTTPException(status_code=403, detail="Account is inactive") from error
    except CartNotFoundError as error:
        raise HTTPException(status_code=404, detail="Cart not found") from error
    except CartClosedError as error:
        raise HTTPException(status_code=409, detail="Cart is no longer active") from error
    except EmptyCartError as error:
        raise HTTPException(status_code=400, detail="Cart is empty") from error
    except MissingAddressError as error:
        raise HTTPException(status_code=400, detail="Delivery address required") from error
    except TotalChangedError as error:
        raise HTTPException(
            status_code=409, 
            detail={"message": "Order total has changed","total": error.total}) from error
    except UnavailableItemError as error:
        raise HTTPException(
            status_code=409, detail="Some items are no longer available") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Order could not be saved") from error