"""Projetos e produtos (RF-004 a RF-008)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_perm
from app.core.roles import P_ANALYSIS_READ, P_PRODUCT_WRITE, P_PROJECT_WRITE
from app.db.session import get_db
from app.models import Product, ProductComponent, ProductImage, Project, User
from app.schemas.api import ImageOut, ProductIn, ProductOut, ProjectIn, ProjectOut
from app.services import storage

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectIn, user: User = Depends(require_perm(P_PROJECT_WRITE)),
    db: Session = Depends(get_db),
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
    user: User = Depends(require_perm(P_ANALYSIS_READ)), db: Session = Depends(get_db)
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.organization_id == user.organization_id)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductIn, user: User = Depends(require_perm(P_PRODUCT_WRITE)),
    db: Session = Depends(get_db),
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
    product_id: str, user: User = Depends(require_perm(P_ANALYSIS_READ)),
    db: Session = Depends(get_db),
) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Produto não encontrado")
    return product


@router.post("/products/{product_id}/images", response_model=ImageOut, status_code=201)
async def upload_image(
    product_id: str,
    image_type: str | None = None,
    file: UploadFile = File(...),
    user: User = Depends(require_perm(P_PRODUCT_WRITE)),
    db: Session = Depends(get_db),
) -> ProductImage:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Produto não encontrado")
    data = await file.read()
    url = storage.save(data, file.filename or "image.png", file.content_type)
    img = ProductImage(product_id=product.id, file_url=url, image_type=image_type)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


@router.get("/products/{product_id}/images", response_model=list[ImageOut])
def list_images(
    product_id: str, user: User = Depends(require_perm(P_ANALYSIS_READ)),
    db: Session = Depends(get_db),
) -> list[ProductImage]:
    return db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
