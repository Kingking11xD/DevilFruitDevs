from pydantic import BaseModel, ConfigDict, Field


class Restaurant(BaseModel):
    id: int
    name: str
    cuisine: str
    address: str


class RestaurantCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid", # accepts only the 3 fields below
        str_strip_whitespace=True,
    )

    name: str = Field(min_length=1, max_length=100)
    cuisine: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=250)