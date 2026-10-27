from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class RestaurantUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    cuisine: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, min_length=1, max_length=250)

    @model_validator(mode="after")
    def check_changes(self) -> "RestaurantUpdate":
        changes = self.model_dump(exclude_unset=True)

        if not changes:
            raise ValueError("Provide at least one field")

        for value in changes.values():
            if value is None:
                raise ValueError("Cannot be null")

        return self