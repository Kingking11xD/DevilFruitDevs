from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.dependencies import get_current_admin, get_restaurant_manager
from app.repositories.restaurant_repo import RestaurantRepo
from app.schemas.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate
from app.services.restaurant_service import RestaurantNotFoundError, RestaurantService

router = APIRouter()

repository = RestaurantRepo()
service = RestaurantService(repository)


@router.get(
    "/restaurants",
    response_model=list[Restaurant],
    summary="List restaurants",
    description="Return all restaurants, optionally filtered by name and cuisine"
)
def get_restaurants(
    search: Annotated[
        str | None,
        Query(description="Search restaurants by name"),
    ] = None,
    cuisine: Annotated[
        str | None,
        Query(description="Filter restaurants by cuisine"),
    ] = None,
) -> list[dict[str, Any]]:
    """Return restaurants that match the optional search and cuisine filters"""
    return service.get_all_restaurants(search=search, cuisine=cuisine)

@router.get(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    summary="View restaurant details",
    description="Return one restaurant using its integer ID.",
    responses={404: {"description": "Restaurant not found"}},
)
def get_restaurant(
    restaurant_id: Annotated[
        int,
        Path(gt=0, description="The restaurant's integer ID"),
    ],
) -> dict[str, Any]:
    try:
        return service.get_restaurant_by_id(restaurant_id)
    except RestaurantNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

@router.post(
    "/restaurants",
    response_model=Restaurant,
    status_code=201,
    summary="Create a restaurant",
    description="An active administrator can save a restaurant with a server-assigned ID.",
    responses={
        401: {"description": "Authentication required or invalid"},
        403: {"description": "Active administrator account required"},
        422: {"description": "Invalid restaurant information"},
        500: {"description": "Restaurant data could not be saved"},
    },
    dependencies=[Depends(get_current_admin)],
)
def create_restaurant(data: RestaurantCreate) -> dict[str, Any]:
    try:
        return service.create_restaurant(
            data.name,
            data.cuisine,
            data.address,
        )
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Restaurant data could not be saved",
        ) from error

@router.patch(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    summary="Update a restaurant",
    description=(
        "An active administrator or restaurant user assigned to this restaurant "
        "can update its fields and receive the saved restaurant. "
        "Missing fields stay unchanged. "
        "Empty updates and null values are rejected."
    ),
    responses={
        401: {"description": "Authentication required or invalid"},
        403: {"description": "Account is inactive or cannot manage this restaurant"},
        404: {"description": "Restaurant not found"},
        422: {"description": "Invalid restaurant information"},
        500: {"description": "Restaurant data not saved"},
    },
    dependencies=[Depends(get_restaurant_manager)],
)
def update_restaurant(
    restaurant_id: Annotated[int, Path(gt=0, description="The restaurant's INT ID")],
    data: RestaurantUpdate) -> dict[str, Any]:
    changes = data.model_dump(exclude_unset=True)

    try:
        return service.update_restaurant(restaurant_id, changes)
    except RestaurantNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Restaurant data not saved",
        ) from error
