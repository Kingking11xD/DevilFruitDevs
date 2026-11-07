from pydantic import BaseModel, ConfigDict, Field, model_validator


class MenuItem(BaseModel):
    id: int
    restaurant_id: int
    name: str
    price: int
    available: bool

class MenuItemCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(min_length=1, max_length=100)
    price: int = Field(gt=0, description="Price in Berries")
    available: bool = True

class MenuItemUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: int | None = Field(default=None, gt=0)
    available: bool | None = None

    @model_validator(mode="after")
    def check_changes(self) -> "MenuItemUpdate":
        changes = self.model_dump(exclude_unset=True)

        if not changes:
            raise ValueError("Provide at least one field")

        for value in changes.values():
            if value is None:
                raise ValueError("Cannot be null")

        return self