"""Catalog domain module: products, pricing, and barcode parsing."""

from server.modules.catalog.models import Product, ProductType
from server.modules.catalog.router import router

__all__ = ["Product", "ProductType", "router"]
