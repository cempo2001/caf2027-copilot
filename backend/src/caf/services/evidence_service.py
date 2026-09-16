"""
EvidenceService — upload dokaza uz podkriterijum (api-contract-v1.md 6.1).

Vault & Documents Agent (CLAUDE.md 7.6). Redoslijed je namjeran:

1. uloga -> SAR (404/409) -> podkriterijum (422)
2. čitanje sa limitom veličine, provjera tipa (ekstenzija + magic bajtovi)
3. SHA-256
4. AV sken — FAIL-CLOSED: skener nedostupan => 503, ništa se ne čuva;
   prijetnja => 422, ništa se ne čuva. `scanner=None` (AV_SCAN_MODE=disabled,
   samo lokalni razvoj) => status `pending`.
5. MinIO (ključ bez korisničkog imena fajla)
6. upis metapodataka; ako upis padne (npr. Approved Lock trigger u
   međuvremenu), objekat se briše — nema "siročića" u trezoru.

Servis ne zna za HTTP: prima bilo šta što ima `filename` i `async read(n)`
(Starlette `UploadFile` to zadovoljava).
"""

import hashlib
import logging
import uuid
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.exceptions import (
    AvScannerUnavailableError,
    EvidenceInfectedError,
    EvidenceTooLargeError,
    EvidenceTypeNotAllowedError,
    InvalidInputError,
    StorageUnavailableError,
)
from caf.core.i18n import Locale
from caf.core.security import TokenPayload
from caf.integrations.clamav import AvScanner, AvScannerError, ScanVerdict
from caf.integrations.object_storage import ObjectStorage, ObjectStorageError
from caf.models import EvidenceFile, StoredAvStatus
from caf.schemas.evidence import EvidenceUploadOut
from caf.services.evidence_files import detect_kind, sanitize_filename
from caf.services.sar_access import EDITOR_ROLES, SarAccess

logger = logging.getLogger(__name__)

_READ_CHUNK = 1024 * 1024


class UploadStream(Protocol):
    filename: str | None

    async def read(self, size: int = -1) -> bytes: ...


class EvidenceService:
    def __init__(
        self,
        session: AsyncSession,
        user: TokenPayload,
        locale: Locale,
        *,
        storage: ObjectStorage,
        scanner: AvScanner | None,
        max_bytes: int,
    ) -> None:
        self._session = session
        self._user = user
        self._locale = locale
        self._storage = storage
        self._scanner = scanner
        self._max_bytes = max_bytes
        self._access = SarAccess(session, user, locale)

    async def upload(self, sar_id: UUID, code: str, upload: UploadStream) -> EvidenceUploadOut:
        self._access.require_role(EDITOR_ROLES)
        sar = await self._access.load_unlocked_sar(sar_id)
        subcriteria = await self._access.load_subcriteria(code)

        filename = sanitize_filename(upload.filename)
        data = await self._read_limited(upload)
        if not data:
            raise InvalidInputError(locale=self._locale)
        kind = detect_kind(filename, data[:4096])
        if kind is None:
            raise EvidenceTypeNotAllowedError(locale=self._locale)

        digest = hashlib.sha256(data).hexdigest()
        av_status = await self._scan(data, digest)

        object_key = f"{sar.institution_id}/{sar.id}/{subcriteria.code}/{uuid.uuid4().hex}"
        try:
            await self._storage.put(
                object_key,
                data,
                content_type=kind.content_type,
                metadata={"sha256": digest, "av-scan-status": av_status.value},
            )
        except ObjectStorageError as exc:
            logger.error("Trezor nedostupan pri uploadu dokaza: %s", exc)
            raise StorageUnavailableError(locale=self._locale) from exc

        record = EvidenceFile(
            self_assessment_id=sar.id,
            institution_id=sar.institution_id,
            subcriteria_code=subcriteria.code,
            original_filename=filename,
            content_type=kind.content_type,
            size_bytes=len(data),
            sha256=digest,
            object_key=object_key,
            av_scan_status=av_status.value,
            uploaded_by=self._user.sub,
        )
        self._session.add(record)
        try:
            await self._access.commit_or_map_lock()
        except Exception:
            await self._discard_object(object_key)
            raise
        await self._session.refresh(record)
        return EvidenceUploadOut(
            id=record.id,
            filename=record.original_filename,
            sha256=record.sha256,
            av_scan_status=av_status.value,
        )

    async def _read_limited(self, upload: UploadStream) -> bytes:
        buffer = bytearray()
        while True:
            chunk = await upload.read(_READ_CHUNK)
            if not chunk:
                return bytes(buffer)
            buffer.extend(chunk)
            if len(buffer) > self._max_bytes:
                raise EvidenceTooLargeError(locale=self._locale)

    async def _scan(self, data: bytes, digest: str) -> StoredAvStatus:
        if self._scanner is None:
            logger.warning(
                "AV_SCAN_MODE=disabled — dokaz %s sačuvan BEZ skeniranja (pending)", digest
            )
            return StoredAvStatus.PENDING
        try:
            result = await self._scanner.scan(data)
        except AvScannerError as exc:
            logger.error("ClamAV nedostupan, upload odbijen (fail-closed): %s", exc)
            raise AvScannerUnavailableError(locale=self._locale) from exc
        if result.verdict is ScanVerdict.INFECTED:
            logger.warning(
                "Odbijen zaražen dokaz sha256=%s potpis=%s korisnik=%s",
                digest,
                result.signature,
                self._user.sub,
            )
            raise EvidenceInfectedError(locale=self._locale)
        return StoredAvStatus.CLEAN

    async def _discard_object(self, object_key: str) -> None:
        try:
            await self._storage.delete(object_key)
        except ObjectStorageError as exc:
            # Ne prikriva originalnu grešku; siroče se bilježi za ručno čišćenje.
            logger.error("Nije obrisan objekat %s poslije neuspjelog upisa: %s", object_key, exc)
