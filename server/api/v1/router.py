from fastapi import APIRouter

from server.api.v1.endpoints import inventory, products, users

router = APIRouter(prefix="/v1")
router.include_router(users.router)
router.include_router(products.router)
router.include_router(inventory.router)
