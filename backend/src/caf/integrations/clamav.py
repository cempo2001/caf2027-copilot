"""
Minimalan async klijent za clamd INSTREAM protokol (TCP).

Vault & Documents Agent (CLAUDE.md 7.6). Namjerno bez dodatne biblioteke:
protokol je jednostavan i stabilan (clamd man stranica, INSTREAM):

    -> b"zINSTREAM\\0"
    -> [uint32 big-endian dužina][podaci] ... (ponavlja se)
    -> b"\\0\\0\\0\\0"                      (kraj)
    <- b"stream: OK\\0"                      čisto
    <- b"stream: <potpis> FOUND\\0"          prijetnja
    <- b"... ERROR\\0"                        greška skenera

Svaka greška veze, timeout ili nerazumljiv odgovor je `AvScannerError` —
servis to tretira kao "skener nedostupan" i NE čuva fajl (fail-closed).
"""

import asyncio
import struct
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

_CHUNK_SIZE = 64 * 1024
_MAX_REPLY_BYTES = 4096


class ScanVerdict(StrEnum):
    CLEAN = "clean"
    INFECTED = "infected"


@dataclass(frozen=True)
class ScanResult:
    verdict: ScanVerdict
    signature: str | None = None


class AvScannerError(Exception):
    """Skener nije dostupan ili je vratio grešku — rezultat skeniranja NE postoji."""


class AvScanner(Protocol):
    async def scan(self, data: bytes) -> ScanResult: ...


def parse_clamd_reply(raw: bytes) -> ScanResult:
    reply = raw.rstrip(b"\0").decode("utf-8", errors="replace").strip()
    # Format: "stream: OK" | "stream: <sig> FOUND" | "<poruka> ERROR"
    _, _, status = reply.partition(": ")
    if reply.endswith(" ERROR") or not status:
        raise AvScannerError(f"clamd greška: {reply!r}")
    if status == "OK":
        return ScanResult(ScanVerdict.CLEAN)
    if status.endswith(" FOUND"):
        return ScanResult(ScanVerdict.INFECTED, status[: -len(" FOUND")].strip() or None)
    raise AvScannerError(f"Nepoznat clamd odgovor: {reply!r}")


class ClamdScanner:
    def __init__(self, host: str, port: int, timeout_seconds: float) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout_seconds

    async def scan(self, data: bytes) -> ScanResult:
        try:
            return await asyncio.wait_for(self._scan(data), timeout=self._timeout)
        except AvScannerError:
            raise
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError) as exc:
            raise AvScannerError(f"clamd nedostupan: {exc!r}") from exc

    async def _scan(self, data: bytes) -> ScanResult:
        reader, writer = await asyncio.open_connection(self._host, self._port)
        try:
            writer.write(b"zINSTREAM\0")
            for offset in range(0, len(data), _CHUNK_SIZE):
                chunk = data[offset : offset + _CHUNK_SIZE]
                writer.write(struct.pack("!L", len(chunk)) + chunk)
                await writer.drain()
            writer.write(struct.pack("!L", 0))
            await writer.drain()

            reply = bytearray()
            while b"\0" not in reply and len(reply) < _MAX_REPLY_BYTES:
                part = await reader.read(1024)
                if not part:
                    break
                reply.extend(part)
            if not reply:
                raise AvScannerError("clamd je zatvorio vezu bez odgovora")
            return parse_clamd_reply(bytes(reply))
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
