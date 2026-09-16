"""
/api/v1/self-assessments/{sar_id}/subcriteria/{code}/ai-consensus
(api-contract-v1.md 4.5).

Kad AI nije korišćen, odgovor je i dalje 200 (source="fallback") uz
header `X-Consensus-Warning: ai_provider_unavailable` — Offline Math
Fallback je normalan put, ne greška (CLAUDE.md 7.5).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from caf.api.deps import get_consensus_service
from caf.schemas.common import ErrorResponse
from caf.schemas.consensus import ConsensusSuggestionOut
from caf.services.consensus_service import ConsensusService

router = APIRouter(prefix="/self-assessments", tags=["ai-consensus"])

WARNING_HEADER = "X-Consensus-Warning"

_ERRORS: dict[int | str, dict[str, object]] = {
    code: {"model": ErrorResponse} for code in (403, 404, 409, 422)
}


@router.post(
    "/{sar_id}/subcriteria/{code}/ai-consensus",
    response_model=ConsensusSuggestionOut,
    responses=_ERRORS,
)
async def request_ai_consensus(
    sar_id: UUID,
    code: str,
    response: Response,
    service: Annotated[ConsensusService, Depends(get_consensus_service)],
) -> ConsensusSuggestionOut:
    result = await service.suggest(sar_id, code)
    if result.provider_unavailable:
        response.headers[WARNING_HEADER] = "ai_provider_unavailable"
    return result.suggestion
