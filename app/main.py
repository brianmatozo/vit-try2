from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.db import Base, engine

app = FastAPI(
    title="backend api",
    description="backend api",
    version="1.0.0",
    contact={
        "name": "support",
        "url": "http://example.com/contact",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

Base.metadata.create_all(bind=engine)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "hello"}
