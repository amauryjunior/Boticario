"""Projetos e produtos (RF-004 a RF-008)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Product, ProductComponent, Project, User
from app.schemas.api import ProductIn, ProductOut, ProjectIn, ProjectOut

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Project:
    project = Project(
        organization_id=user.organization_id, name=body.name,
        objective=body.objective, target_market=body.target_market, created_by=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.organization_id == user.organization_id)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Product:
    project = db.get(Project, body.project_id)
    if not project or project.organization_id != user.organization_id:
        raise HTTPException(404, "Projeto não encontrado")
    product = Product(
        project_id=project.id, name=body.name, brand=body.brand, category=body.category,
        description=body.description, target_user=body.target_user, country=body.country,
        lifecycle_stage=body.lifecycle_stage, cap_type=body.cap_type,
    )
    db.add(product)
    db.flush()
    for c in body.components:
        db.add(ProductComponent(product_id=product.id, **c.model_dump()))
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Produto não encontrado")
    return product
