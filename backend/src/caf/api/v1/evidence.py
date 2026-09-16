"""
/api/v1/self-assessments/{sar_id}/subcriteria/{code}/evidence — upload
dokaza (api-contract-v1.md 6.1). Multipart polje: `file`.

Router je TANAK: prosleđuje `UploadFile` servisu (koji ga vidi samo kao
tok sa `filename` i `read()`), domenske greške mapira main.py.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from caf.api.deps import get_evidence_service
from caf.schemas.common import ErrorResponse
from caf.schemas.evidence import EvidenceUploadOut
from caf.services.evidence_service import EvidenceService

router = APIRouter(prefix="/self-assessments", tags=["evidence"])

# Brojevi umjesto `status.HTTP_422_*` konstanti — Starlette je preimenovao 422
# konstantu između verzija (deprecation upozorenje).
_ERRORS: dict[int | str, dict[str, object]] = {
    code: {"model": ErrorResponse} for code in (403, 404, 409, 422, 503)
}


@router.post(
    "/{sar_id}/subcriteria/{code}/evidence",
    response_model=EvidenceUploadOut,
    status_code=status.HTTP_201_CREATED,
    responses=_ERRORS,
)
async def upload_evidence(
    sar_id: UUID,
    code: str,
    file: Annotated[UploadFile, File(description="Fajl dokaza (max 25 MB)")],
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
) -> EvidenceUploadOut:
    try:
        return await service.upload(sar_id, code, file)
    finally:
        await file.close()
