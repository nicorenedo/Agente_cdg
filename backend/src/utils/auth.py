"""
auth.py — Control de acceso por perfil de usuario

Dos perfiles:
  - UserRole.GESTOR        : Solo su propia cartera, precios STD, comparativas anónimas
  - UserRole.CONTROL_GESTION : Acceso completo sin restricciones
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Roles
# ─────────────────────────────────────────────

class UserRole(Enum):
    GESTOR = "gestor"
    CONTROL_GESTION = "control_gestion"


# ─────────────────────────────────────────────
# Guard principal
# ─────────────────────────────────────────────

class AccessGuard:
    """
    Punto único de control de acceso para todos los agentes y endpoints.

    Uso básico:
        guard = AccessGuard()
        guard.require_own_gestor(role, user_gestor_id=18, target_gestor_id=5)  # raise si gestor != 5
        allowed = guard.can_access_gestor(role, user_gestor_id=18, target_gestor_id=18)  # True
    """

    # Palabras clave que indican intento de acceder a otro gestor
    _CROSS_GESTOR_PATTERNS = [
        r"gestor\s+(\d+)",
        r"del\s+gestor\s+(\d+)",
        r"datos.*gestor\s+(\d+)",
        r"compara.*gestor\s+(\d+)",
        r"performance.*gestor\s+(\d+)",
    ]

    # ── Permisos básicos ──────────────────────────────────────────────

    def is_cdg(self, role: UserRole) -> bool:
        return role == UserRole.CONTROL_GESTION

    def is_gestor(self, role: UserRole) -> bool:
        return role == UserRole.GESTOR

    def can_access_gestor(
        self,
        role: UserRole,
        user_gestor_id: Optional[Union[str, int]],
        target_gestor_id: Optional[Union[str, int]],
    ) -> bool:
        """True si el rol/usuario puede acceder a los datos de target_gestor_id."""
        if role == UserRole.CONTROL_GESTION:
            return True
        # Gestor solo puede ver sus propios datos
        if user_gestor_id is None or target_gestor_id is None:
            return True  # sin info suficiente, no bloquear
        return str(user_gestor_id) == str(target_gestor_id)

    def require_own_gestor(
        self,
        role: UserRole,
        user_gestor_id: Optional[Union[str, int]],
        target_gestor_id: Optional[Union[str, int]],
    ) -> None:
        """Lanza PermissionError si el acceso no está permitido."""
        if not self.can_access_gestor(role, user_gestor_id, target_gestor_id):
            raise PermissionError(
                f"Acceso denegado: el gestor {user_gestor_id} no puede "
                f"acceder a datos del gestor {target_gestor_id}."
            )

    def require_cdg(self, role: UserRole) -> None:
        """Lanza PermissionError si el rol no es CDG/Dirección."""
        if role != UserRole.CONTROL_GESTION:
            raise PermissionError(
                "Acceso denegado: este recurso requiere perfil de Control de Gestión."
            )

    # ── Filtrado de datos ─────────────────────────────────────────────

    def filter_gestor_list(
        self,
        rows: List[Dict[str, Any]],
        role: UserRole,
        user_gestor_id: Optional[Union[str, int]],
    ) -> List[Dict[str, Any]]:
        """
        Filtra una lista de filas con campo GESTOR_ID para que el perfil
        gestor solo vea sus propias filas.
        """
        if role == UserRole.CONTROL_GESTION or user_gestor_id is None:
            return rows
        uid = str(user_gestor_id)
        return [
            row for row in rows
            if str(row.get("GESTOR_ID", row.get("gestor_id", uid))) == uid
        ]

    def strip_confidential_fields(
        self,
        row: Dict[str, Any],
        role: UserRole,
    ) -> Dict[str, Any]:
        """
        Elimina campos confidenciales (precios REAL) para perfil gestor.
        CDG conserva todos los campos.
        """
        if role == UserRole.CONTROL_GESTION:
            return row
        confidential = {
            "PRECIO_MANTENIMIENTO_REAL",
            "precio_mantenimiento_real",
            "PRECIO_REAL",
            "precio_real",
        }
        return {k: v for k, v in row.items() if k not in confidential}

    def filter_rows_confidential(
        self,
        rows: List[Dict[str, Any]],
        role: UserRole,
    ) -> List[Dict[str, Any]]:
        """Aplica strip_confidential_fields a cada fila de la lista."""
        if role == UserRole.CONTROL_GESTION:
            return rows
        return [self.strip_confidential_fields(r, role) for r in rows]

    # ── Detección de intento cross-gestor en texto libre ─────────────

    def extract_target_gestor_from_message(
        self, message: str
    ) -> Optional[int]:
        """
        Detecta si el mensaje solicita datos de un gestor concreto.
        Devuelve su ID entero, o None si no se detecta.
        """
        msg_lower = message.lower()
        for pattern in self._CROSS_GESTOR_PATTERNS:
            match = re.search(pattern, msg_lower)
            if match and match.groups():
                return int(match.group(1))
        return None

    def check_message_permission(
        self,
        message: str,
        role: UserRole,
        user_gestor_id: Optional[Union[str, int]],
    ) -> Dict[str, Any]:
        """
        Verifica si el mensaje es compatible con el rol del usuario.
        Devuelve {'allowed': bool, 'reason': str, 'target_gestor': int|None}.
        """
        target = self.extract_target_gestor_from_message(message)

        if target is None:
            return {"allowed": True, "reason": "ok", "target_gestor": None}

        if role == UserRole.CONTROL_GESTION:
            return {"allowed": True, "reason": "cdg_full_access", "target_gestor": target}

        allowed = self.can_access_gestor(role, user_gestor_id, target)
        return {
            "allowed": allowed,
            "reason": "own_data" if allowed else "cross_gestor_blocked",
            "target_gestor": target,
        }

    # ── SQL guard por perfil ──────────────────────────────────────────

    def build_gestor_where_clause(
        self, gestor_id: Union[str, int]
    ) -> str:
        """Devuelve la cláusula WHERE para filtrar por gestor en SQL dinámico."""
        return f"WHERE g.GESTOR_ID = {int(gestor_id)}"

    def inject_gestor_filter(
        self,
        sql: str,
        role: UserRole,
        user_gestor_id: Optional[Union[str, int]],
    ) -> str:
        """
        Para perfil gestor, añade/refuerza el filtro GESTOR_ID en la query.
        Estrategia conservadora: si ya contiene un WHERE, añade AND; si no, añade WHERE.
        Solo aplica si el SQL hace referencia a MAESTRO_GESTORES o GESTOR_ID.
        """
        if role == UserRole.CONTROL_GESTION or user_gestor_id is None:
            return sql

        gestor_filter = f"g.GESTOR_ID = {int(user_gestor_id)}"

        if "GESTOR_ID" not in sql.upper():
            logger.warning("SQL sin referencia a GESTOR_ID — no se inyecta filtro")
            return sql

        # Si ya tiene el filtro del gestor correcto, no duplicar
        if str(user_gestor_id) in sql and "GESTOR_ID" in sql.upper():
            return sql

        # Añadir al final como condición extra (JOIN o subquery protegen mejor,
        # pero esto es una salvaguarda de última línea)
        if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
            sql = re.sub(
                r"\bWHERE\b",
                f"WHERE {gestor_filter} AND ",
                sql,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            sql = sql.rstrip(";") + f" WHERE {gestor_filter}"

        logger.info(f"🔐 Filtro gestor {user_gestor_id} inyectado en SQL")
        return sql

    # ── Determinación de rol por user_id ─────────────────────────────

    @staticmethod
    def determine_role(user_id: Optional[str]) -> UserRole:
        """
        Heurística simple para determinar el rol a partir del user_id.
        Prefijos reconocidos: 'gestor-*' → GESTOR, cualquier otro → CONTROL_GESTION.
        """
        if not user_id:
            return UserRole.CONTROL_GESTION
        uid = str(user_id).lower()
        if uid.startswith("gestor"):
            return UserRole.GESTOR
        return UserRole.CONTROL_GESTION

    @staticmethod
    def extract_gestor_id_from_user_id(user_id: Optional[str]) -> Optional[str]:
        """Extrae el gestor_id de un user_id con formato 'gestor-{id}-*'."""
        if not user_id:
            return None
        match = re.search(r"gestor[-_](\d+)", str(user_id), re.IGNORECASE)
        return match.group(1) if match else None


# ─────────────────────────────────────────────
# Instancia global
# ─────────────────────────────────────────────

access_guard = AccessGuard()

__all__ = ["UserRole", "AccessGuard", "access_guard"]
