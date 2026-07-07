"""Modelos ORM (subconjunto do modelo de dados do documento de requisitos)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plan: Mapped[str] = mapped_column(String(40), default="starter")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="gestor_marca")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    organization: Mapped["Organization"] = relationship(back_populates="users")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_market: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="ativo")
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_user: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(60), nullable=True)
    lifecycle_stage: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cap_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    images: Mapped[list["ProductImage"]] = relationship(back_populates="product")
    components: Mapped[list["ProductComponent"]] = relationship(back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    file_url: Mapped[str] = mapped_column(String(500))
    image_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    product: Mapped["Product"] = relationship(back_populates="images")


class ProductComponent(Base):
    __tablename__ = "product_components"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    component_type: Mapped[str] = mapped_column(String(60))
    material: Mapped[str | None] = mapped_column(String(120), nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="components")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued")
    score_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    maturity_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    profiles: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV de perfis
    engine: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(60), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    checklist: Mapped[list["ChecklistItem"]] = relationship(back_populates="run")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="run")
    traces: Mapped[list["AgentTrace"]] = relationship(back_populates="run")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(80))
    item: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40))  # atende | parcial | nao_atende | ...
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    run: Mapped["AnalysisRun"] = relationship(back_populates="checklist")


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    component: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrier: Mapped[str] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(String(120), nullable=True)
    option_min: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_mid: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_premium: Mapped[str | None] = mapped_column(Text, nullable=True)
    effort: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    standard_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    standard_status: Mapped[str | None] = mapped_column(String(40), nullable=True)

    run: Mapped["AnalysisRun"] = relationship(back_populates="recommendations")


class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(80))
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    run: Mapped["AnalysisRun"] = relationship(back_populates="traces")


class StandardReference(Base):
    __tablename__ = "standard_references"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="referencia_design")
    applicability_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    format: Mapped[str] = mapped_column(String(20), default="json")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
