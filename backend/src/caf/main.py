"""
FastAPI app factory — CAF 2027 Copilot backend.

CLAUDE.md Sekcija 3: globalni exception handleri ovde su JEDINO mjesto
gdje se domenski izuzeci (caf.core.exceptions) mapiraju na HTTP odgovore
— routeri i servisi ih samo podižu, ne hvataju.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from caf.api.v1.router import api_router
from caf.core.config import get_settings
from caf.core.exceptions import CafDomainError
from caf.core.i18n import translate
from caf.core.security import InvalidTokenError


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CAF 2027 Copilot API",
        version="0.1.0",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Fazi 5: zamijeniti pravim domenom
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.exception_handler(CafDomainError)
    async def handle_domain_error(_: Request, exc: CafDomainError) -> JSONResponse:
        """
        Mapira domenske greške na lokalizovan JSON odgovor.
        Primer: SarLockedError -> 409 sa porukom na jeziku iz JWT-a
        (CLAUDE.md Sekcija 3 pravilo 3 + Sekcija 6.1).
        """
        message = exc.detail or translate(exc.i18n_key, exc.locale)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.i18n_key, "message": message},
        )

    @app.exception_handler(InvalidTokenError)
    async def handle_invalid_token(_: Request, exc: InvalidTokenError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_token", "message": str(exc)},
        )

    return app


app = create_app()
