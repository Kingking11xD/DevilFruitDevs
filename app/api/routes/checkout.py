from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_customer
from app.schemas.order import CheckoutRequest, Order
from app.services.checkout_service import (
    CheckoutService, EmptyCartError, InactiveCustomerError, MissingAddressError,
    NoActiveCartError, TotalChangedError, UnavailableItemError)

router = APIRouter()


def get_checkout_service() -> CheckoutService:
    """Create the checkout service. Tests replace this with isolated data."""
    return CheckoutService()


@router.post(
    "/customers/me/checkout",
    response_model=Order,
    status_code=201,
    summary="Check out my cart",
    description="Turn the signed-in customer's active cart into a saved order. "
    "Send the total the customer saw in their cart as expected_total. "
    "Prices and availability are rechecked against current menu data; if the total "
    "has changed, nothing is saved so the customer can review their cart. "
    "The cart is closed only once the order is saved.",
    responses={
        400: {"description": "Cart is empty or no delivery address is set"},
        401: {"description": "Authentication required or invalid"},
        403: {"description": "Account is inactive or is not a customer account"},
        404: {"description": "No active cart"},
        409: {"description": "A menu item or the restaurant is no longer available, or the total has changed"},
        500: {"description": "Order could not be saved"},
    },
)
def checkout(
        data: CheckoutRequest,
        account: Annotated[dict[str, Any], Depends(get_current_customer)],
        service: Annotated[CheckoutService, Depends(get_checkout_service)]) -> dict[str, Any]:
    try:
        return service.checkout(account["id"], data.expected_total)
    except InactiveCustomerError as error:
        raise HTTPException(status_code=403, detail="Account is inactive") from error
    except NoActiveCartError as error:
        raise HTTPException(status_code=404, detail="No active cart") from error
    except EmptyCartError as error:
        raise HTTPException(status_code=400, detail="Cart is empty") from error
    except MissingAddressError as error:
        raise HTTPException(status_code=400, detail="Delivery address required") from error
    except TotalChangedError as error:
        raise HTTPException(
            status_code=409, detail="Order total has changed, please review your cart") from error
    except UnavailableItemError as error:
        raise HTTPException(
            status_code=409, detail="Some items are no longer available") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Order could not be saved") from error