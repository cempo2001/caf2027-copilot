"""
/api/v1/self-assessments/{sar_id}/cip — CIP akcioni plan (api-contract-v1.md 5).

Router je TANAK: validacija (Pydantic) -> servis -> DTO. Domenske greške
(409/403/404/422) mapira globalni handler u main.py.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from caf.api.deps import get_cip_service
from caf.schemas.cip import CipItemCreate, CipItemOut, CipListOut
from caf.schemas.common import ErrorResponse
from caf.services.cip_service import CipService

router = APIRouter(prefix="/self-assessments", tags=["cip"])

_ERRORS = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
}


@router.get(
    "/{sar_id}/cip",
    response_model=CipListOut,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def list_cip_items(
    sar_id: UUID,
    service: Annotated[CipService, Depends(get_cip_service)],
) -> CipListOut:
    return await service.list_items(sar_id)


@router.post(
    "/{sar_id}/cip",
    response_model=CipItemOut,
    status_code=status.HTTP_201_CREATED,
    responses=_ERRORS,
)
async def create_cip_item(
    sar_id: UUID,
    payload: CipItemCreate,
    service: Annotated[CipService, Depends(get_cip_service)],
) -> CipItemOut:
    return await service.create_item(sar_id, payload)
