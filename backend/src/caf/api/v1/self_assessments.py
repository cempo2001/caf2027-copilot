"""
/api/v1/self-assessments — SAR rute (api-contract-v1.md, sekcija 4).

Router je TANAK: validira ulaz (Pydantic), poziva servis, vraća DTO.
Nema poslovne logike, nema SQL-a, nema hvatanja domenskih izuzetaka —
to radi globalni handler u main.py (409/403/404/422).

Rute 4.5 (ai-consensus), 5 (CIP) i 6 (evidence) su u zasebnim routerima
(`consensus.py`, `cip.py`, `evidence.py`) — isti prefiks, odvojeni moduli.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from caf.api.deps import get_sar_service
from caf.schemas.common import ErrorResponse, Page
from caf.schemas.self_assessment import (
    ApproveResponse,
    SarDetail,
    SarSummary,
    SubcriteriaScoreOut,
    SubcriteriaScoreUpdate,
)
from caf.services.sar_service import SarService

router = APIRouter(prefix="/self-assessments", tags=["self-assessments"])

_LOCKED = {status.HTTP_409_CONFLICT: {"model": ErrorResponse}}
_FORBIDDEN = {status.HTTP_403_FORBIDDEN: {"model": ErrorResponse}}
_NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}


@router.get("", response_model=Page[SarSummary])
async def list_self_assessments(
    service: Annotated[SarService, Depends(get_sar_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[SarSummary]:
    return await service.list_self_assessments(page=page, page_size=page_size)


@router.post(
    "",
    response_model=SarSummary,
    status_code=status.HTTP_201_CREATED,
    responses=_FORBIDDEN,
)
async def create_self_assessment(
    service: Annotated[SarService, Depends(get_sar_service)],
) -> SarSummary:
    return await service.create_self_assessment()


@router.get("/{sar_id}", response_model=SarDetail, responses=_NOT_FOUND)
async def get_self_assessment(
    sar_id: UUID,
    service: Annotated[SarService, Depends(get_sar_service)],
) -> SarDetail:
    return await service.get_detail(sar_id)


@router.patch(
    "/{sar_id}/subcriteria/{code}",
    response_model=SubcriteriaScoreOut,
    responses={**_LOCKED, **_FORBIDDEN, **_NOT_FOUND},
)
async def update_subcriteria(
    sar_id: UUID,
    code: str,
    payload: SubcriteriaScoreUpdate,
    service: Annotated[SarService, Depends(get_sar_service)],
) -> SubcriteriaScoreOut:
    return await service.update_subcriteria(sar_id, code, payload)


@router.post(
    "/{sar_id}/approve",
    response_model=ApproveResponse,
    responses={**_LOCKED, **_FORBIDDEN, **_NOT_FOUND},
)
async def approve_self_assessment(
    sar_id: UUID,
    service: Annotated[SarService, Depends(get_sar_service)],
) -> ApproveResponse:
    return await service.approve(sar_id)
