"""Autenticação: signup, login e /me (RF-001, RF-003)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perm
from app.core.roles import ALL_ROLES, P_ADMIN
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Organization, User
from app.schemas.api import LoginIn, MeOut, SignupIn, TokenOut, UserCreateIn

router = APIRouter(tags=["auth"])


@router.post("/auth/signup", response_model=TokenOut, status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)) -> TokenOut:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    org = Organization(name=body.organization_name)
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id, name=body.name, email=body.email,
        password_hash=hash_password(body.password), role="administrador",
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.id, org.id, user.role)
    return TokenOut(access_token=token)


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")
    token = create_access_token(user.id, user.organization_id, user.role)
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/users", response_model=MeOut, status_code=201)
def create_user(
    body: UserCreateIn,
    admin: User = Depends(require_perm(P_ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    """Admin cria usuário na própria organização com um papel (RF-001/RF-002)."""
    if body.role not in ALL_ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Papel inválido")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    user = User(
        organization_id=admin.organization_id, name=body.name, email=body.email,
        password_hash=hash_password(body.password), role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
