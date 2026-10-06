from pydantic import BaseModel


class MenuItem(BaseModel):
    id: int
    restaurant_id: int
    name: str
    price: float
    available: bool = True