from fastapi import APIRouter

from server.modules.catalog.router import router as catalog_router
from server.modules.identity.router import router as identity_router
from server.modules.inventory.router import router as inventory_router

router = APIRouter(prefix="/v1")
router.include_router(identity_router)
router.include_router(catalog_router)
router.include_router(inventory_router)
