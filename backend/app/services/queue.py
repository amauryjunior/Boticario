"""Fila de análise: Pub/Sub em produção, thread em processo no local.

Mantém o mesmo contrato dos dois lados: `enqueue_analysis` publica/agenda e
`process_analysis` executa a malha de agentes e persiste o resultado.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AnalysisRun, Product
from app.services.analysis_service import execute_analysis

log = logging.getLogger("inclua.queue")


def process_analysis(run_id: str) -> None:
    """Processa uma análise a partir do seu id (usado pelo worker/thread)."""
    db = SessionLocal()
    try:
        run = db.get(AnalysisRun, run_id)
        if not run or run.status == "done":
            return
        product = db.get(Product, run.product_id)
        if not product:
            run.status = "error"
            db.commit()
            return
        run.status = "running"
        db.commit()
        execute_analysis(db, run, product)
    except Exception as exc:  # pragma: no cover
        log.exception("Falha ao processar análise %s: %s", run_id, exc)
        run = db.get(AnalysisRun, run_id)
        if run:
            run.status = "error"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _publish_pubsub(run_id: str) -> None:
    from google.cloud import pubsub_v1  # type: ignore

    publisher = pubsub_v1.PublisherClient()
    topic = publisher.topic_path(settings.google_cloud_project, settings.pubsub_topic)
    publisher.publish(topic, json.dumps({"run_id": run_id}).encode("utf-8"))


def enqueue_analysis(run_id: str) -> None:
    """Enfileira a análise conforme o backend configurado."""
    if settings.queue_backend == "pubsub":
        try:
            _publish_pubsub(run_id)
            return
        except Exception as exc:  # pragma: no cover
            log.warning("Pub/Sub indisponível (%s); processando em thread local.", exc)
    # Local: processa em thread separada (não bloqueia a resposta HTTP).
    threading.Thread(target=process_analysis, args=(run_id,), daemon=True).start()
