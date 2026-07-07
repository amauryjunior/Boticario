"""RAG normativo: embeddings + busca vetorial sobre trechos de normas.

- Embeddings: Vertex AI `text-embedding-004` quando configurado; senão um
  embedding local determinístico (hashing bag-of-words) para funcionar offline.
- Busca: cosseno em Python (portável SQLite/Postgres). Em produção com Cloud SQL,
  trocar por consulta pgvector (`embedding <=> query` + índice HNSW) — ver
  docs/inclua-beauty/02-instalacao-gcp.md §5.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import StandardChunk

_LOCAL_DIM = 256


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zà-ú0-9]+", text.lower())


def _local_embed(text: str) -> list[float]:
    """Embedding determinístico offline (hashing de tokens em vetor fixo)."""
    vec = [0.0] * _LOCAL_DIM
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % _LOCAL_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _vertex_embed(text: str) -> list[float] | None:
    try:
        from google import genai  # type: ignore

        client = genai.Client(
            vertexai=settings.google_genai_use_vertexai.upper() == "TRUE",
            project=settings.google_cloud_project or None,
            location=settings.google_cloud_location or None,
            api_key=settings.google_api_key or None,
        )
        resp = client.models.embed_content(
            model="text-embedding-004", contents=text
        )
        return list(resp.embeddings[0].values)
    except Exception:
        return None


def embed(text: str) -> list[float]:
    if settings.analysis_engine == "adk":
        v = _vertex_embed(text)
        if v:
            return v
    return _local_embed(text)


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def search(db: Session, query: str, jurisdiction: str | None = None, k: int = 4) -> list[dict]:
    """Retorna os k trechos normativos mais relevantes para a consulta."""
    q = db.query(StandardChunk)
    if jurisdiction:
        q = q.filter(StandardChunk.jurisdiction == jurisdiction)
    rows = q.all()
    if not rows:
        return []
    qv = embed(query)
    scored = []
    for r in rows:
        if not r.embedding:
            continue
        score = _cosine(qv, json.loads(r.embedding))
        scored.append((score, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {"title": r.title, "source": r.source, "status": r.status,
         "jurisdiction": r.jurisdiction, "chunk": r.chunk, "score": round(s, 4)}
        for s, r in scored[:k] if s > 0
    ]


# Corpus normativo inicial (resumos/paráfrases com status — RF-016).
NORM_CORPUS = [
    ("WCAG 2.2 — Contraste", "WCAG22", "UE/US", "referencia_design",
     "Texto deve ter contraste mínimo de 4,5:1 (AA) para leitura por pessoas com "
     "baixa visão. Aplicável a rótulos digitais, QR e interfaces."),
    ("WCAG 2.2 — Tamanho de alvo", "WCAG22", "UE/US", "referencia_design",
     "Alvos de toque/interação devem ter tamanho mínimo adequado, beneficiando "
     "pessoas com destreza reduzida."),
    ("LBI 13.146/2015 — Acessibilidade", "LBI", "BR", "aplicavel_com_ressalva",
     "A Lei Brasileira de Inclusão assegura acessibilidade e autonomia; produtos "
     "devem considerar identificação e uso independente por pessoas com deficiência."),
    ("ANVISA — Rotulagem de cosméticos", "ANVISA", "BR", "pendente_validacao",
     "A rotulagem de cosméticos deve conter informações obrigatórias legíveis. "
     "Acessibilidade da informação (fonte, contraste, braille) deve ser validada "
     "com a legislação vigente."),
    ("EAA — Diretiva UE 2019/882", "EAA", "UE", "aplicavel_com_ressalva",
     "O European Accessibility Act define requisitos de acessibilidade para "
     "produtos e serviços comercializados na UE, incluindo informação acessível."),
    ("ABNT NBR 9050 — Identificação tátil", "NBR9050", "BR", "referencia_design",
     "Recomenda sinalização tátil e elementos de relevo para orientação e "
     "identificação por pessoas com deficiência visual."),
    ("Design inclusivo — Feedback multisensorial", "GUIDE", "GLOBAL", "referencia_design",
     "Fornecer feedback tátil, sonoro e visual redundante melhora a usabilidade "
     "para pessoas cegas, surdas e com deficiência cognitiva."),
    ("Design inclusivo — Abertura de embalagem", "GUIDE", "GLOBAL", "referencia_design",
     "Tampas que exigem baixa força e boa aderência (flip-top, press-to-open, "
     "asas, textura antiderrapante) favorecem artrite e destreza reduzida."),
]


def seed_chunks(db: Session) -> int:
    if db.query(StandardChunk).count() > 0:
        return 0
    n = 0
    for title, source, jur, status, text in NORM_CORPUS:
        db.add(StandardChunk(
            title=title, source=source, jurisdiction=jur, status=status,
            chunk=text, embedding=json.dumps(embed(f"{title}. {text}")),
        ))
        n += 1
    db.commit()
    return n
