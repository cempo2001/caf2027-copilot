"""
Custom exception klase — mapiraju se na HTTP status kodove u
`main.py` exception handler-ima (CLAUDE.md Sekcija 3, pravilo 3).

Servisni sloj podiže ove izuzetke; router sloj ih nikad ne hvata
pojedinačno — globalni handler u main.py to radi na jednom mjestu.
"""

from caf.core.i18n import Locale


class CafDomainError(Exception):
    """Bazna klasa za sve domenske greške aplikacije."""

    i18n_key: str = "validation_error"
    status_code: int = 400

    def __init__(self, *, locale: Locale, detail: str | None = None) -> None:
        self.locale = locale
        self.detail = detail
        super().__init__(detail or self.i18n_key)


class SarLockedError(CafDomainError):
    """
    409 Conflict — pokušaj izmjene odobrenog (Approved Lock) SAR-a.
    CLAUDE.md Sekcija 3, pravilo 3.
    """

    i18n_key = "sar_locked"
    status_code = 409


class TenantMismatchError(CafDomainError):
    """403 Forbidden — pristup resursu van sopstvenog tenant-a (RLS narušavanje)."""

    i18n_key = "tenant_mismatch"
    status_code = 403


class InvalidCredentialsError(CafDomainError):
    """401 Unauthorized."""

    i18n_key = "invalid_credentials"
    status_code = 401


class NotFoundError(CafDomainError):
    """
    404 — resurs ne postoji ILI ga RLS ne prikazuje. Namjerno ista
    poruka za oba slučaja: ne otkrivamo postojanje tuđih resursa
    (docs/api-contract-v1.md, 1.3).
    """

    i18n_key = "not_found"
    status_code = 404


class InsufficientRoleError(CafDomainError):
    """403 — rola korisnika nema ovlašćenje (npr. approve bez Sponsor role)."""

    i18n_key = "insufficient_role"
    status_code = 403


class SarIncompleteError(CafDomainError):
    """403 — approve prije nego što je svih 28 podkriterijuma ocijenjeno."""

    i18n_key = "sar_incomplete"
    status_code = 403


class UnknownSubcriteriaError(CafDomainError):
    """422 — šifra podkriterijuma nije u zvaničnom CAF okviru."""

    i18n_key = "unknown_subcriteria"
    status_code = 422


class AiProviderUnavailableError(CafDomainError):
    """
    503 Service Unavailable — signal da je konsenzus servis prešao na
    Offline Math Fallback. Ovo NIJE greška koja prekida tok; koristi se
    da API sloj može vratiti informativni header/poruku korisniku,
    dok se odgovor i dalje uspješno vraća sa fallback rezultatom.
    """

    i18n_key = "ai_provider_unavailable"
    status_code = 503
