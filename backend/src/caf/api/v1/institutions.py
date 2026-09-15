"""GET /api/v1/institutions/me (api-contract-v1.md, 3.1)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from caf.api.deps import get_institution_service
from caf.schemas.institution import InstitutionOut
from caf.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/me", response_model=InstitutionOut)
async def get_my_institution(
    service: Annotated[InstitutionService, Depends(get_institution_service)],
) -> InstitutionOut:
    return await service.get_mine()
