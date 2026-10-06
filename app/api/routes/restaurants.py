from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query

from app.repositories.restaurant_repo import RestaurantRepo
from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import RestaurantNotFoundError, RestaurantService

router = APIRouter()

repository = RestaurantRepo("data/restaurants.json")
service = RestaurantService(repository)


@router.get(
        "/restaurants",
        response_model=list[Restaurant],
        summary="List restaurants",
        description="Return all restaurants, optionally filtered by name using the search parameter"
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
