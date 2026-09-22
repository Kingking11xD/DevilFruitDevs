from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.restaurants import router as restaurants_router

app = FastAPI()

app.include_router(health_router)
app.include_router(restaurants_router)
