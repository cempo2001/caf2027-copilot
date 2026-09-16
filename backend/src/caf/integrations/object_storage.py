"""
Dokazni trezor — MinIO (S3) adapter.

Vault & Documents Agent (CLAUDE.md 7.6). `minio` klijent je sinhron, pa
se pozivi izvršavaju u thread pool-u (`asyncio.to_thread`) da ne blokiraju
event loop. Pozivi su sa imenovanim argumentima u obliku minio 7.2.x API-ja
(`metadata=`); minio 8 (master grana) mijenja potpise, zato je zavisnost
ograničena na `<8` u pyproject.toml. Svaka greška (mreža, S3, kredencijali) postaje
`ObjectStorageError` — servis je mapira na 503 i ništa ne upisuje u bazu.
"""

import asyncio
import io
from typing import Protocol

import urllib3
from minio import Minio


class ObjectStorageError(Exception):
    """Trezor nije dostupan ili je odbio operaciju."""


class ObjectStorage(Protocol):
    async def put(
        self, key: str, data: bytes, *, content_type: str, metadata: dict[str, str]
    ) -> None: ...

    async def delete(self, key: str) -> None: ...


class MinioObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
    ) -> None:
        http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=5.0, read=60.0),
            retries=urllib3.Retry(
                total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]
            ),
        )
        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            http_client=http_client,
        )
        self._bucket = bucket
        self._bucket_ready = False
        self._bucket_lock = asyncio.Lock()

    async def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        async with self._bucket_lock:
            if self._bucket_ready:
                return
            exists = await asyncio.to_thread(
                lambda: self._client.bucket_exists(bucket_name=self._bucket)
            )
            if not exists:
                await asyncio.to_thread(lambda: self._client.make_bucket(bucket_name=self._bucket))
            self._bucket_ready = True

    async def put(
        self, key: str, data: bytes, *, content_type: str, metadata: dict[str, str]
    ) -> None:
        try:
            await self._ensure_bucket()
            await asyncio.to_thread(
                lambda: self._client.put_object(
                    bucket_name=self._bucket,
                    object_name=key,
                    data=io.BytesIO(data),
                    length=len(data),
                    content_type=content_type,
                    metadata=metadata,
                )
            )
        except Exception as exc:  # minio.S3Error, urllib3 greške, OSError
            raise ObjectStorageError(f"MinIO put nije uspio: {exc!r}") from exc

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(
                lambda: self._client.remove_object(bucket_name=self._bucket, object_name=key)
            )
        except Exception as exc:
            raise ObjectStorageError(f"MinIO delete nije uspio: {exc!r}") from exc
