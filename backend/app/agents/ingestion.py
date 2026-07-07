"""Agente de ingestão multimodal: extrai atributos da embalagem a partir de
imagem + texto usando Gemini (Vertex AI). Offline retorna None (sem enriquecer).
"""
from __future__ import annotations

import json
import logging

from pydantic import BaseModel

from app.core.config import settings

log = logging.getLogger("inclua.ingestion")


class IngestionResult(BaseModel):
    category: str | None = None
    cap_type: str | None = None
    detected_components: list[str] = []
    observations: str | None = None


_PROMPT = (
    "Você é o Agente de Ingestão da Inclua Beauty. Analise a imagem da embalagem "
    "de beleza e o texto fornecido. Extraia: categoria (perfumes, maquiagem, "
    "skincare, cabelos, corpo, infantil, masculino, 60+, pet, acessorios); "
    "tipo de tampa (rosca, flip_top, press_to_open, spray, pump, outro); "
    "componentes visíveis (frasco, tampa, rotulo, valvula, atomizador, pump, "
    "caixa, folheto, aplicador, lacre, refil); e observações de acessibilidade. "
    "Responda estritamente no schema."
)


def available() -> bool:
    try:
        import google.genai  # noqa: F401
    except Exception:
        return False
    return bool(
        settings.google_api_key or settings.google_genai_use_vertexai.upper() == "TRUE"
    )


def ingest(image_bytes: bytes, mime: str, product_text: str) -> IngestionResult | None:
    """Extrai atributos multimodais. Retorna None se indisponível/erro."""
    if not available():
        return None
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        client = genai.Client(
            vertexai=settings.google_genai_use_vertexai.upper() == "TRUE",
            project=settings.google_cloud_project or None,
            location=settings.google_cloud_location or None,
            api_key=settings.google_api_key or None,
        )
        resp = client.models.generate_content(
            model=settings.model_fast,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime),
                f"{_PROMPT}\n\nTexto do produto:\n{product_text}",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IngestionResult,
            ),
        )
        return IngestionResult.model_validate_json(resp.text)
    except Exception as exc:  # pragma: no cover - depende de credenciais externas
        log.warning("Ingestão multimodal falhou: %s", exc)
        return None
