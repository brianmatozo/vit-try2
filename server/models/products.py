from starlette.middleware.base import BaseHTTPMiddleware
from server.core.db import Base


class Product(Base):
    """Database model representing a created product."""

    __tablename__ = "products"
    BaseHTTPMiddleware
