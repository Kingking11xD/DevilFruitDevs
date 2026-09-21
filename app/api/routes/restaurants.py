from fastapi import APIRouter

from app.schemas.restaurant import Restaurant

router = APIRouter()

@router.get("/restaurants", response_model=list[Restaurant])
def get_restaurants():
    return []