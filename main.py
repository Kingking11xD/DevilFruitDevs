from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.customers import router as customers_router
from app.api.routes.health import router as health_router
from app.api.routes.menu import router as menu_router
from app.api.routes.restaurants import router as restaurants_router

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    details = []

    # leave submitted values out so errors do not expose passwords
    for problem in error.errors():
        details.append({
            "type": problem["type"],
            "loc": problem["loc"],
            "msg": problem["msg"]})

    return JSONResponse(status_code=422, content={"detail": details})


#Frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(restaurants_router)
app.include_router(menu_router)
app.include_router(customers_router)
app.include_router(auth_router)
