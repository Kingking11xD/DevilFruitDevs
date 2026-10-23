from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, status

from app.api.routes.restaurants import repository as restaurant_repository
from app.repositories.menu_repo import MenuRepo
from app.schemas.menu import MenuItem, MenuItemCreate, MenuItemUpdate
from app.services.menu_service import MenuItemNotFoundError, MenuService
from app.services.restaurant_service import RestaurantNotFoundError

router = APIRouter()

menu_repository = MenuRepo()

service = MenuService(
    menu_repository,
    restaurant_repository,
)


@router.get(
    "/restaurants/{restaurant_id}/menu-items",
    response_model=list[MenuItem],
    summary="View a restaurant's menu",
    description=(
        "Return all menu items for a restaurant, ordered by item ID. "
        "Unavailable items are included with available set to false. "
        "A restaurant with no items returns an empty list."
    ),
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


@router.get(
    "/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=MenuItem,
    summary="View a menu item",
    description=(
        "Return one menu item. The item must belong to the restaurant "
        "in the URL, otherwise it is reported as not found."
    ),
    responses={404: {"description": "Restaurant or menu item not found"}},
)
def get_menu_item(
    restaurant_id: Annotated[
        int,
        Path(gt=0, description="The restaurant's integer ID"),
    ],
    item_id: Annotated[
        int,
        Path(gt=0, description="The menu item's integer ID"),
    ],
) -> dict[str, Any]:

    try:
        return service.get_menu_item(restaurant_id, item_id)

    except (RestaurantNotFoundError, MenuItemNotFoundError) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

@router.post(
    "/restaurants/{restaurant_id}/menu-items",
    response_model=MenuItem,
    status_code=status.HTTP_201_CREATED,
    summary="Add a menu item",
    responses={404: {"description": "Restaurant not found"}},
)
def add_menu_item(
    restaurant_id: Annotated[int, Path(gt=0)],
    body: MenuItemCreate,
) -> dict:
    try:
        return service.add_menu_item(restaurant_id, body.model_dump())
    except RestaurantNotFoundError:
        raise HTTPException(status_code=404, detail="Restaurant not found")


@router.patch(
    "/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=MenuItem,
    summary="Update menu item",
    responses={404: {"description": "Restaurant or menu item not found"}},
)
def update_menu_item(
    restaurant_id: Annotated[int, Path(gt=0)],
    item_id: Annotated[int, Path(gt=0)],
    body: MenuItemUpdate,
) -> dict:
    try:
        return service.update_menu_item(
            restaurant_id, item_id, body.model_dump(exclude_none=True)
        )
    except RestaurantNotFoundError:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    except MenuItemNotFoundError:
        raise HTTPException(status_code=404, detail="Menu item not found")