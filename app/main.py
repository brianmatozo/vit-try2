from fastapi import FastAPI

from app.core.db import Base, engine

app = FastAPI(
    title="My Super API",
    description="A modern, high-performance API built with FastAPI.",
    version="1.0.0",
    contact={
        "name": "API Support",
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


@app.get("/")
def root():
    return {"message": "hello"}
