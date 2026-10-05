from fastapi import APIRouter

from app.schemas.restaurant import Restaurant
from app.repositories.restaurant_repo import RestaurantRepo
from app.services.restaurant_service import RestaurantService

router = APIRouter()

repository = RestaurantRepo("data/restaurants.json")
service = RestaurantService(repository)


@router.get("/restaurants", response_model=list[Restaurant])
def get_restaurants():
    return service.get_all_restaurants()