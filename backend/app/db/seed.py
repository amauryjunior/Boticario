"""Seed de dados de demonstração (org + usuário + projeto + produto exemplo)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents import knowledge as kb
from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    Organization,
    Product,
    ProductComponent,
    Project,
    StandardReference,
    User,
)


def seed_demo(db: Session) -> None:
    if db.query(User).filter(User.email == settings.demo_email).first():
        return

    org = Organization(name="Marca Demo Beauty", plan="professional")
    db.add(org)
    db.flush()

    db.add(User(
        organization_id=org.id, name="Usuário Demo", email=settings.demo_email,
        password_hash=hash_password(settings.demo_password), role="administrador",
    ))

    project = Project(
        organization_id=org.id, name="Linha Perfumes 2026",
        objective="Avaliar acessibilidade do portfólio de perfumes",
        target_market="BR",
    )
    db.add(project)
    db.flush()

    product = Product(
        project_id=project.id, name="Perfume Aurora 100ml", brand="Demo Beauty",
        category="perfumes", description="Frasco de vidro com tampa de rosca e atomizador.",
        target_user="adulto", country="BR", cap_type="rosca",
    )
    db.add(product)
    db.flush()
    for ct in ["frasco", "tampa", "rotulo", "valvula", "atomizador", "caixa", "folheto"]:
        db.add(ProductComponent(product_id=product.id, component_type=ct))

    # Base normativa inicial com status (RF-016)
    for key, meta in kb.STANDARDS.items():
        db.add(StandardReference(
            title=meta["ref"], source=key, jurisdiction="BR/UE", status=meta["status"]
        ))

    db.commit()
