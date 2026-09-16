"""Agregator svih v1 ruta. Nove rute se registruju SAMO ovdje."""

from fastapi import APIRouter

from caf.api.v1 import auth, cip, consensus, evidence, institutions, self_assessments

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(institutions.router)
api_router.include_router(self_assessments.router)
api_router.include_router(consensus.router)
api_router.include_router(cip.router)
api_router.include_router(evidence.router)
