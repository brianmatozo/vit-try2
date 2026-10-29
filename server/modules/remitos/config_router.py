from fastapi import APIRouter

from server.core.config import settings
from server.modules.remitos.schemas import (
    RemitoConfigDTO,
    RemitoConfigUpdate,
)

router = APIRouter(tags=["remitos"])


@router.get("/remitos/config", response_model=RemitoConfigDTO)
async def get_config():
    return RemitoConfigDTO(
        has_api_key=bool(settings.openrouter_api_key),
        primary_model=settings.openrouter_primary_model,
        fallback_model=settings.openrouter_fallback_model,
    )


@router.post("/remitos/config", response_model=RemitoConfigDTO)
async def update_config(req: RemitoConfigUpdate):
    if req.api_key is not None:
        settings.openrouter_api_key = req.api_key
    if req.primary_model is not None:
        settings.openrouter_primary_model = req.primary_model
    return RemitoConfigDTO(
        has_api_key=bool(settings.openrouter_api_key),
        primary_model=settings.openrouter_primary_model,
        fallback_model=settings.openrouter_fallback_model,
    )
