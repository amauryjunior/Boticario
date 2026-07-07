"""Abstração de armazenamento de objetos: local (default) ou Google Cloud Storage."""
from __future__ import annotations

import os
import uuid

from app.core.config import settings


def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1] or ".bin"


def save(data: bytes, filename: str, content_type: str | None = None) -> str:
    """Persiste o objeto e retorna uma URL/URI para referência."""
    key = f"{uuid.uuid4().hex}{_ext(filename)}"
    if settings.gcs_bucket:
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client()
            blob = client.bucket(settings.gcs_bucket).blob(key)
            blob.upload_from_string(data, content_type=content_type)
            return f"gs://{settings.gcs_bucket}/{key}"
        except Exception:
            pass  # fallback para local
    os.makedirs(settings.uploads_dir, exist_ok=True)
    path = os.path.join(settings.uploads_dir, key)
    with open(path, "wb") as fh:
        fh.write(data)
    return f"file://{os.path.abspath(path)}"


def read(url: str) -> bytes:
    """Lê o objeto a partir da URL/URI retornada por save()."""
    if url.startswith("gs://"):
        from google.cloud import storage  # type: ignore

        _, _, rest = url.partition("gs://")
        bucket, _, key = rest.partition("/")
        client = storage.Client()
        return client.bucket(bucket).blob(key).download_as_bytes()
    path = url.replace("file://", "")
    with open(path, "rb") as fh:
        return fh.read()
