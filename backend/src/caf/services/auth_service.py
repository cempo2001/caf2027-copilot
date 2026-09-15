"""
AuthService — login i izdavanje JWT-a sa custom claims.

Backend Agent (CLAUDE.md 7.3). Servis ne zna za HTTP: prima podatke,
vraća DTO, podiže domenske izuzetke. Router ih mapira.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.config import Settings
from caf.core.exceptions import InvalidCredentialsError
from caf.core.i18n import Locale
from caf.core.passwords import hash_password, needs_rehash, verify_password
from caf.core.security import Role, create_access_token
from caf.schemas.auth import LoginResponse, UserOut

# Heš "lažne" lozinke — verify se izvršava i kad korisnik NE postoji,
# da vrijeme odgovora ne otkriva da li email postoji (timing oracle).
_DUMMY_HASH = hash_password("caf2027-dummy-password-for-constant-time")


@dataclass(frozen=True)
class _LookupRow:
    id: UUID
    institution_id: UUID
    hashed_password: str
    role: str
    lang: str


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def login(self, *, email: str, password: str, lang: Locale) -> LoginResponse:
        """
        Login NEMA tenant kontekst (još ne znamo instituciju) — zato ide
        kroz `auth_lookup_user()` (migracija 0002, SECURITY DEFINER), ne
        kroz direktan SELECT nad `users` koji bi RLS vratio prazan.
        """
        row = await self._lookup(email)

        if row is None:
            verify_password(password, _DUMMY_HASH)  # constant-time putanja
            raise InvalidCredentialsError(locale=lang)
        if not verify_password(password, row.hashed_password):
            raise InvalidCredentialsError(locale=lang)

        if needs_rehash(row.hashed_password):
            await self._rehash(row, password)

        # Jezik izabran pri loginu postaje claim i pamti se na korisniku
        # (CLAUDE.md 6.2) — sledeći login bez eksplicitnog izbora ga zatiče.
        await self._persist_lang(row, lang)

        role = Role(row.role)
        token = create_access_token(
            settings=self._settings,
            user_id=row.id,
            institution_id=row.institution_id,
            role=role,
            lang=lang,
        )
        return LoginResponse(
            access_token=token,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
            user=UserOut(
                id=row.id,
                email=email,
                role=role,
                institution_id=row.institution_id,
                lang=lang,
            ),
        )

    async def _lookup(self, email: str) -> _LookupRow | None:
        result = await self._session.execute(
            text(
                "SELECT id, institution_id, hashed_password, role::text AS role, lang "
                "FROM auth_lookup_user(CAST(:email AS text))"
            ),
            {"email": email},
        )
        record = result.mappings().first()
        return _LookupRow(**record) if record else None

    async def _rehash(self, row: _LookupRow, password: str) -> None:
        await self._session.execute(
            text("SELECT auth_update_user_login(CAST(:uid AS uuid), CAST(:hash AS text), NULL)"),
            {"uid": str(row.id), "hash": hash_password(password)},
        )
        await self._session.commit()

    async def _persist_lang(self, row: _LookupRow, lang: Locale) -> None:
        if row.lang == lang:
            return
        await self._session.execute(
            text("SELECT auth_update_user_login(CAST(:uid AS uuid), NULL, CAST(:lang AS text))"),
            {"uid": str(row.id), "lang": lang},
        )
        await self._session.commit()
