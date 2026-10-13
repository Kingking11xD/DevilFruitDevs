from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    id: int
    restaurant_id: int
    name: str
    price: int
    available: bool

class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: int = Field(gt=0, description="Price in Berries")
    available: bool = True