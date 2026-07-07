"""Dependências de API: sessão de DB e usuário autenticado (JWT)."""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.roles import has_perm
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado")
    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado")
    return user


def require_perm(perm: str) -> Callable[..., User]:
    """Dependência que exige a permissão `perm` para o papel do usuário (RF-002)."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if not has_perm(user.role, perm):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Papel '{user.role}' não tem permissão para esta ação ({perm}).",
            )
        return user

    return checker
