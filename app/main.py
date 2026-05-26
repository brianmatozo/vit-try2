from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.db import Base, engine

_tags_metadata: list[dict[str, str]] = [
    {
        "name": "Users",
        "description": "Create, read, update, and delete user accounts.",
    },
]

app = FastAPI(
    title="Vitalcer API",
    description=(
        "Backend API for the Vitalcer e-commerce platform. "
        "Provides endpoints for managing users, products, orders, and more."
    ),
    version="1.0.0",
    contact={
        "name": "Vitalcer Support",
        "url": "http://example.com/contact",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=_tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

Base.metadata.create_all(bind=engine)

app.include_router(v1_router, prefix="/api")
