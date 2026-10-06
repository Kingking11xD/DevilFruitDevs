from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path

from app.repositories.menu_repo import MenuRepo
from app.repositories.restaurant_repo import RestaurantRepo
from app.schemas.menu import MenuItem
from app.services.menu_service import (
    MenuService,
    RestaurantNotFoundError,
)

router = APIRouter()

menu_repository = MenuRepo("data/menu_items.json")
restaurant_repository = RestaurantRepo("data/restaurants.json")

service = MenuService(
    menu_repository,
    restaurant_repository,
)

@router.get(
    "/restaurants/{restaurant_id}/menu",
    response_model=list[MenuItem],
    summary="View a restaurant's menu",
    description="Return all menu items for a restaurant, ordered by item ID.",
    responses={404: {"description": "Restaurant not found"}},
)
def get_menu(
    restaurant_id: Annotated[
        int,
        Path(gt=0, description="The restaurant's integer ID"),
    ],
) -> list[dict[str, Any]]:

    try:
        return service.get_menu(restaurant_id)

    except RestaurantNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error