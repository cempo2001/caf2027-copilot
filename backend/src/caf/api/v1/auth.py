"""POST /api/v1/auth/login — jedina ruta bez JWT-a (api-contract-v1.md, 2.1)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from caf.api.deps import get_auth_service
from caf.schemas.auth import LoginRequest, LoginResponse
from caf.schemas.common import ErrorResponse
from caf.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
async def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return await service.login(email=payload.email, password=payload.password, lang=payload.lang)
