"""
Čista pravila za fajlove dokaza — bez I/O, lako testabilna.

Vault & Documents Agent (CLAUDE.md 7.6). Tip fajla se NE vjeruje
klijentskom Content-Type-u: dozvoljava se po ekstenziji, a sadržaj mora
imati odgovarajući "magic" potpis (preimenovan izvršni fajl ne prolazi).
Sačuvani content-type je naš, iz tabele ispod.
"""

import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # stari MS Office (doc/xls/ppt)
_ZIP = b"PK\x03\x04"  # OOXML i ODF su ZIP kontejneri


@dataclass(frozen=True)
class FileKind:
    content_type: str
    magic: tuple[bytes, ...] | None  # None = tekstualni fajl (provjera: bez NUL bajtova)


ALLOWED_KINDS: dict[str, FileKind] = {
    "pdf": FileKind("application/pdf", (b"%PDF-",)),
    "doc": FileKind("application/msword", (_OLE,)),
    "xls": FileKind("application/vnd.ms-excel", (_OLE,)),
    "ppt": FileKind("application/vnd.ms-powerpoint", (_OLE,)),
    "docx": FileKind(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", (_ZIP,)
    ),
    "xlsx": FileKind("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", (_ZIP,)),
    "pptx": FileKind(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation", (_ZIP,)
    ),
    "odt": FileKind("application/vnd.oasis.opendocument.text", (_ZIP,)),
    "ods": FileKind("application/vnd.oasis.opendocument.spreadsheet", (_ZIP,)),
    "odp": FileKind("application/vnd.oasis.opendocument.presentation", (_ZIP,)),
    "png": FileKind("image/png", (b"\x89PNG\r\n\x1a\n",)),
    "jpg": FileKind("image/jpeg", (b"\xff\xd8\xff",)),
    "jpeg": FileKind("image/jpeg", (b"\xff\xd8\xff",)),
    "txt": FileKind("text/plain; charset=utf-8", None),
    "csv": FileKind("text/csv; charset=utf-8", None),
}

_FORBIDDEN_CHARS = set('<>:"/\\|?*')
_MAX_FILENAME = 255
_FALLBACK_STEM = "dokaz"


def sanitize_filename(raw: str | None) -> str:
    """Samo ime (bez putanje), bez kontrolnih/nedozvoljenih znakova, ≤255."""
    name = PurePosixPath((raw or "").replace("\\", "/")).name
    name = unicodedata.normalize("NFC", name)
    name = "".join(ch for ch in name if ch.isprintable() and ch not in _FORBIDDEN_CHARS)
    name = name.strip(" .")
    if not name:
        return _FALLBACK_STEM
    if len(name) > _MAX_FILENAME:
        stem, dot, ext = name.rpartition(".")
        if dot and 0 < len(ext) <= 10:
            name = stem[: _MAX_FILENAME - len(ext) - 1] + "." + ext
        else:
            name = name[:_MAX_FILENAME]
    return name


def extension_of(filename: str) -> str:
    stem, dot, ext = filename.rpartition(".")
    return ext.lower() if dot and stem else ""


def detect_kind(filename: str, head: bytes) -> FileKind | None:
    """Vraća dozvoljeni tip ili None (ekstenzija nije dozvoljena ili sadržaj ne odgovara)."""
    kind = ALLOWED_KINDS.get(extension_of(filename))
    if kind is None:
        return None
    if kind.magic is None:
        return None if b"\x00" in head else kind
    return kind if any(head.startswith(sig) for sig in kind.magic) else None
