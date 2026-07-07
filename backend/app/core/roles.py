"""Papéis de acesso e permissões (RF-002).

Cada papel recebe um conjunto de permissões nomeadas. Os endpoints exigem
permissões via a dependência `require_perm` (app/api/deps.py).
"""
from __future__ import annotations

# Papéis
ADMIN = "administrador"
GESTOR = "gestor_marca"
DESIGNER = "designer"
ESPECIALISTA = "especialista"
REGULATORIO = "regulatorio"
TESTADOR = "testador_pcd"
LEITOR = "cliente_leitor"

ALL_ROLES = [ADMIN, GESTOR, DESIGNER, ESPECIALISTA, REGULATORIO, TESTADOR, LEITOR]

# Permissões nomeadas
P_PROJECT_WRITE = "project:write"
P_PRODUCT_WRITE = "product:write"
P_ANALYSIS_RUN = "analysis:run"
P_ANALYSIS_READ = "analysis:read"
P_REPORT_WRITE = "report:write"
P_STANDARDS_READ = "standards:read"
P_STANDARDS_WRITE = "standards:write"
P_ADMIN = "admin:manage"

# Matriz papel -> permissões
ROLE_PERMISSIONS: dict[str, set[str]] = {
    ADMIN: {
        P_PROJECT_WRITE, P_PRODUCT_WRITE, P_ANALYSIS_RUN, P_ANALYSIS_READ,
        P_REPORT_WRITE, P_STANDARDS_READ, P_STANDARDS_WRITE, P_ADMIN,
    },
    GESTOR: {
        P_PROJECT_WRITE, P_PRODUCT_WRITE, P_ANALYSIS_RUN, P_ANALYSIS_READ,
        P_REPORT_WRITE, P_STANDARDS_READ,
    },
    DESIGNER: {
        P_PRODUCT_WRITE, P_ANALYSIS_RUN, P_ANALYSIS_READ, P_REPORT_WRITE,
        P_STANDARDS_READ,
    },
    ESPECIALISTA: {
        P_ANALYSIS_RUN, P_ANALYSIS_READ, P_REPORT_WRITE,
        P_STANDARDS_READ, P_STANDARDS_WRITE,
    },
    REGULATORIO: {
        P_ANALYSIS_READ, P_REPORT_WRITE, P_STANDARDS_READ, P_STANDARDS_WRITE,
    },
    TESTADOR: {P_ANALYSIS_READ, P_STANDARDS_READ},
    LEITOR: {P_ANALYSIS_READ, P_STANDARDS_READ},
}


def has_perm(role: str, perm: str) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, set())
