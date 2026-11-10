from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_customer
from app.repositories.order_repo import OrderRepo
from app.schemas.order import Order
from app.services.order_service import OrderNotFoundError, OrderService

router = APIRouter()

AUTH_ERRORS = {
    401: {"description": "Authentication required or invalid"},
    403: {"description": "Account is inactive or is not a customer account"},
    500: {"description": "Orders could not be loaded"},
}

def get_order_service() -> OrderService:
    """Create the order service. Tests replace this with isolated data."""
    return OrderService(OrderRepo())


@router.get(
    "/customers/me/orders",
    response_model=list[Order],
    summary="View my order history",
    description="Return the signed-in customer's orders, newest first. "
    "A customer with no orders gets an empty list.",
    responses=AUTH_ERRORS,
)
def list_my_orders(
        account: Annotated[dict[str, Any], Depends(get_current_customer)],
        service: Annotated[OrderService, Depends(get_order_service)]) -> list[dict[str, Any]]:
    try:
        return service.list_for_customer(account["id"])
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Orders could not be loaded") from error


@router.get(
    "/customers/me/orders/{order_id}",
    response_model=Order,
    summary="View one of my orders",
    description="Return one of the signed-in customer's orders with the item, price "
    "and address details saved at checkout.",
    responses={
        **AUTH_ERRORS,
        404: {"description": "Order not found (or it belongs to another customer)"},
    },
)
def get_my_order(
        order_id: int,
        account: Annotated[dict[str, Any], Depends(get_current_customer)],
        service: Annotated[OrderService, Depends(get_order_service)]) -> dict[str, Any]:
    try:
        return service.get_for_customer(account["id"], order_id)
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail="Order not found") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Orders could not be loaded") from error