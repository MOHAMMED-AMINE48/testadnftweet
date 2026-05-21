"""SQLite repository for project column configuration."""

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from db_sqlite import close_connection, get_connection
from services.master_schema import (
    AUTO_COLUMNS,
    STANDARD_COLUMNS_ORDER,
    STANDARD_COLUMNS_WITH_ROLES,
    get_column_section,
    get_column_roles,
)


@dataclass
class ProjectColumn:
    id: Optional[int]
    project_id: int
    column_name: str
    owner_role: str
    is_auto: int = 0
    display_order: int = 0
    custom_section: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "ProjectColumn":
        keys = set(row.keys()) if hasattr(row, "keys") else set(dict(row).keys())
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            column_name=row["column_name"],
            owner_role=row["owner_role"] if "owner_role" in keys else cls._derive_owner_from_db(row),
            is_auto=row["is_auto"],
            display_order=row["display_order"],
            custom_section=row["custom_section"] if "custom_section" in keys else None,
        )

    @staticmethod
    def _derive_owner_from_db(row) -> str:
        if int(row["is_auto"] or 0):
            return "AUTO"
        roles = get_column_roles(row["column_name"])
        if len(roles) == 1:
            return roles[0]
        if "BUYER" in roles:
            return "BUYER"
        if roles:
            return "MULTI"
        return "CUSTOM"

    @property
    def label(self) -> str:
        return self.column_name


class ProjectColumnRepository:
    """CRUD for project_columns."""

    @staticmethod
    def _normalize_role(role: str) -> str:
        return str(role).strip().upper()

    @staticmethod
    def _normalize_roles(owner_roles: Optional[Iterable[str]] = None, owner_role: Optional[str] = None) -> List[str]:
        roles: List[str] = []
        if owner_role:
            normalized = str(owner_role).strip().upper()
            if normalized:
                roles = [normalized]
        elif owner_roles is not None:
            seen = set()
            for role in owner_roles:
                normalized = str(role).strip().upper()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    roles.append(normalized)
        return roles

    @staticmethod
    def _derive_owner_role(roles: Sequence[str], is_auto: int) -> str:
        if is_auto:
            return "AUTO"
        if not roles:
            return "UNKNOWN"
        if len(roles) == 1:
            return roles[0]
        if "BUYER" in roles:
            return "BUYER"
        return "MULTI"

    @staticmethod
    def _ensure_permissions_table(conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                owner_role TEXT,
                is_auto INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL,
                UNIQUE(project_id, column_name)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_column_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                role TEXT NOT NULL,
                can_edit INTEGER NOT NULL DEFAULT 1,
                UNIQUE(project_id, column_name, role),
                FOREIGN KEY (project_id, column_name) REFERENCES project_columns(project_id, column_name) ON DELETE CASCADE
            )
            """
        )
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(project_columns)")
        column_names = {row["name"] for row in cur.fetchall()}
        if "owner_role" not in column_names:
            conn.execute("ALTER TABLE project_columns ADD COLUMN owner_role TEXT")
        if "custom_section" not in column_names:
            conn.execute("ALTER TABLE project_columns ADD COLUMN custom_section TEXT")

    def clear_project_columns(self, project_id: int) -> None:
        conn = get_connection()
        try:
            with conn:
                self._ensure_permissions_table(conn)
                conn.execute("DELETE FROM project_columns WHERE project_id = ?", (project_id,))
                conn.execute("DELETE FROM project_column_permissions WHERE project_id = ?", (project_id,))
        finally:
            close_connection(conn)

    def insert_column(self, project_id: int, column_name: str, is_auto: int, display_order: int) -> None:
        roles = get_column_roles(column_name)
        owner_role = self._derive_owner_role(roles, int(is_auto))
        conn = get_connection()
        try:
            with conn:
                self._ensure_permissions_table(conn)
                conn.execute(
                    """
                    INSERT INTO project_columns (
                        project_id, column_name, owner_role, is_auto, display_order, custom_section
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, column_name) DO UPDATE SET
                        owner_role = excluded.owner_role,
                        is_auto = excluded.is_auto,
                        display_order = excluded.display_order,
                        custom_section = excluded.custom_section
                    """,
                    (project_id, str(column_name).strip(), owner_role, int(is_auto), int(display_order), get_column_section(str(column_name).strip())),
                )
        finally:
            close_connection(conn)

    def add_permission(self, project_id: int, column_name: str, role: str, can_edit: int = 1) -> None:
        normalized_role = self._normalize_role(role)
        if not normalized_role or normalized_role == "AUTO":
            return
        conn = get_connection()
        try:
            with conn:
                self._ensure_permissions_table(conn)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO project_column_permissions (
                        project_id, column_name, role, can_edit
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (project_id, str(column_name).strip(), normalized_role, int(can_edit)),
                )
        finally:
            close_connection(conn)

    def initialize_standard_columns(self, project_id: int, replace: bool = False) -> None:
        """Seed a project from the fixed master schema and its role permissions."""
        if replace:
            self.clear_project_columns(project_id)

        conn = get_connection()
        try:
            with conn:
                self._ensure_permissions_table(conn)
                for idx, col_def in enumerate(STANDARD_COLUMNS_WITH_ROLES):
                    col_name = col_def["name"]
                    is_auto = 1 if col_def["is_auto"] else 0
                    owner_role = self._derive_owner_role(col_def["roles"], is_auto)
                    conn.execute(
                        """
                        INSERT INTO project_columns (
                            project_id, column_name, owner_role, is_auto, display_order, custom_section
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(project_id, column_name) DO UPDATE SET
                            owner_role = excluded.owner_role,
                            is_auto = excluded.is_auto,
                            display_order = excluded.display_order,
                            custom_section = excluded.custom_section
                        """,
                        (project_id, col_name, owner_role, is_auto, idx, col_def["section"]),
                    )
                    conn.execute(
                        """
                        DELETE FROM project_column_permissions
                        WHERE project_id = ? AND column_name = ?
                        """,
                        (project_id, col_name),
                    )
                    for role in col_def["roles"]:
                        normalized_role = self._normalize_role(role)
                        if normalized_role and normalized_role != "AUTO":
                            conn.execute(
                                """
                                INSERT OR IGNORE INTO project_column_permissions (
                                    project_id, column_name, role, can_edit
                                ) VALUES (?, ?, ?, 1)
                                """,
                                (project_id, col_name, normalized_role),
                            )
        finally:
            close_connection(conn)

    def insert(
        self,
        project_id: int,
        column_name: str,
        owner_roles: Optional[Iterable[str]] = None,
        is_auto: int = 0,
        display_order: int = 0,
        can_edit: int = 1,
        owner_role: Optional[str] = None,
        custom_section: Optional[str] = None,
    ) -> List[ProjectColumn]:
        """Insert or update one project column and its edit permissions."""
        normalized_column = str(column_name).strip()
        if not normalized_column:
            return []

        roles = self._normalize_roles(owner_roles=owner_roles, owner_role=owner_role)
        primary_owner_role = self._derive_owner_role(roles, int(is_auto))
        section = str(custom_section or get_column_section(normalized_column)).strip() or "CUSTOMIZED COLUMNS"

        conn = get_connection()
        try:
            cur = conn.cursor()
            self._ensure_permissions_table(conn)
            cur.execute(
                """
                INSERT INTO project_columns (
                    project_id, column_name, owner_role, is_auto, display_order, custom_section
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, column_name) DO UPDATE SET
                    owner_role = excluded.owner_role,
                    is_auto = excluded.is_auto,
                    display_order = excluded.display_order,
                    custom_section = excluded.custom_section
                """,
                (project_id, normalized_column, primary_owner_role, int(is_auto), int(display_order), section),
            )

            cur.execute(
                "DELETE FROM project_column_permissions WHERE project_id = ? AND column_name = ?",
                (project_id, normalized_column),
            )

            if not int(is_auto):
                for role in roles:
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO project_column_permissions (
                            project_id, column_name, role, can_edit
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (project_id, normalized_column, role, int(can_edit)),
                    )

            conn.commit()
            cur.execute(
                """
                SELECT *
                FROM project_columns
                WHERE project_id = ? AND column_name = ?
                """,
                (project_id, normalized_column),
            )
            row = cur.fetchone()
            return [ProjectColumn.from_row(row)] if row else []
        finally:
            close_connection(conn)

    def replace_project_columns(
        self,
        project_id: int,
        role_columns,
        custom_columns=None,
    ):
        """Backward-compatible API used by existing flows."""
        self.clear_project_columns(project_id)
        self.initialize_standard_columns(project_id)
        display_order = len(STANDARD_COLUMNS_ORDER)

        for custom in custom_columns or []:
            custom_name = str(custom.get("column_name", "")).strip()
            custom_role = str(custom.get("owner_role", "UNKNOWN")).strip().upper() or "UNKNOWN"
            if custom_name:
                self.insert(project_id, custom_name, owner_role=custom_role, is_auto=0, display_order=display_order)
                display_order += 1

    def get_columns(self, project_id: int) -> List[dict]:
        return [
            {
                "id": column.id,
                "project_id": column.project_id,
                "column_name": column.column_name,
                "owner_role": column.owner_role,
                "is_auto": column.is_auto,
                "display_order": column.display_order,
                "custom_section": column.custom_section,
            }
            for column in self.get_project_columns(project_id)
        ]

    def get_project_columns(self, project_id: int) -> List[ProjectColumn]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM project_columns
                WHERE project_id = ?
                ORDER BY display_order, column_name, owner_role
                """,
                (project_id,),
            )
            return [ProjectColumn.from_row(row) for row in cur.fetchall()]
        finally:
            close_connection(conn)

    def get_columns_for_role(self, project_id: int, role: str) -> List[str]:
        return self.get_editable_columns(project_id, role)

    def get_roles_for_column(self, project_id: int, column_name: str) -> List[str]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            self._ensure_permissions_table(conn)
            cur.execute(
                """
                SELECT role
                FROM project_column_permissions
                WHERE project_id = ? AND column_name = ? AND can_edit = 1
                ORDER BY role
                """,
                (project_id, str(column_name).strip()),
            )
            return [row["role"] for row in cur.fetchall()]
        finally:
            close_connection(conn)

    def update_column(self, project_id: int, column_name: str, is_auto: int, display_order: int) -> None:
        self.insert_column(project_id, column_name, int(is_auto), int(display_order))

    def set_permissions(self, project_id: int, column_name: str, permissions: dict) -> None:
        normalized_column = str(column_name).strip()
        conn = get_connection()
        try:
            with conn:
                self._ensure_permissions_table(conn)
                conn.execute(
                    "DELETE FROM project_column_permissions WHERE project_id = ? AND column_name = ?",
                    (project_id, normalized_column),
                )
                for role, can_edit in permissions.items():
                    normalized_role = self._normalize_role(role)
                    if normalized_role and normalized_role != "AUTO" and bool(can_edit):
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO project_column_permissions (
                                project_id, column_name, role, can_edit
                            ) VALUES (?, ?, ?, 1)
                            """,
                            (project_id, normalized_column, normalized_role),
                        )
        finally:
            close_connection(conn)

    def get_editable_columns(self, project_id: int, role: str) -> List[str]:
        role_upper = self._normalize_role(role)
        conn = get_connection()
        try:
            cur = conn.cursor()
            self._ensure_permissions_table(conn)
            if role_upper == "ADMIN":
                cur.execute(
                    """
                    SELECT DISTINCT column_name, display_order
                    FROM project_columns
                    WHERE project_id = ? AND is_auto = 0
                    ORDER BY display_order, column_name
                    """,
                    (project_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT DISTINCT pc.column_name, pc.display_order
                    FROM project_columns pc
                    JOIN project_column_permissions pcp
                      ON pcp.project_id = pc.project_id
                     AND pcp.column_name = pc.column_name
                    WHERE pc.project_id = ?
                      AND pc.is_auto = 0
                      AND pcp.role = ?
                      AND pcp.can_edit = 1
                    ORDER BY display_order, column_name
                    """,
                    (project_id, role_upper),
                )

            return [row["column_name"] for row in cur.fetchall() if row["column_name"] not in AUTO_COLUMNS]
        except Exception:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT column_name, display_order
                FROM project_columns
                WHERE project_id = ?
                  AND is_auto = 0
                  AND (
                      ? = 'ADMIN'
                      OR owner_role = ?
                      OR owner_role = 'MULTI'
                  )
                ORDER BY display_order, column_name
                """,
                (project_id, role_upper, role_upper),
            )
            return [row["column_name"] for row in cur.fetchall() if row["column_name"] not in AUTO_COLUMNS]
        finally:
            close_connection(conn)

    def is_column_editable(self, project_id: int, column_name: str, role: str) -> bool:
        """
        Vérifie si un rôle peut éditer une colonne donnée pour un projet.
        
        Args:
            project_id: ID du projet
            column_name: Nom de la colonne
            role: Rôle utilisateur (BUYER, CAPACITY_MANAGER, SQD, ADMIN, etc.)
            
        Returns:
            True si la colonne est éditable par ce rôle, False sinon
        """
        role_upper = self._normalize_role(role)
        
        # Admin peut éditer toutes les colonnes (sauf auto)
        if role_upper == "ADMIN":
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT 1 FROM project_columns
                    WHERE project_id = ? AND column_name = ? AND is_auto = 0
                    LIMIT 1
                    """,
                    (project_id, str(column_name).strip()),
                )
                return cur.fetchone() is not None
            finally:
                close_connection(conn)
        
        # Pour les autres rôles, vérifier les permissions
        conn = get_connection()
        try:
            cur = conn.cursor()
            self._ensure_permissions_table(conn)
            cur.execute(
                """
                SELECT 1 FROM project_column_permissions
                WHERE project_id = ? AND column_name = ? AND role = ? AND can_edit = 1
                LIMIT 1
                """,
                (project_id, str(column_name).strip(), role_upper),
            )
            return cur.fetchone() is not None
        finally:
            close_connection(conn)

    def get_display_order(self, project_id: int) -> List[str]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT column_name, MIN(display_order) AS ord
                FROM project_columns
                WHERE project_id = ?
                GROUP BY column_name
                ORDER BY ord, column_name
                """,
                (project_id,),
            )
            return [row["column_name"] for row in cur.fetchall()]
        finally:
            close_connection(conn)

    def get_visible_columns_for_role(self, project_id: int, role: str) -> List[ProjectColumn]:
        role_columns = set(self.get_editable_columns(project_id, role))
        return [column for column in self.get_project_columns(project_id) if column.column_name in role_columns]

    def get_readonly_columns(self, project_id: int) -> List[ProjectColumn]:
        return [column for column in self.get_project_columns(project_id) if column.is_auto]

    def add_custom_column(self, project_id: int, column_name: str, owner_role: str = "UNKNOWN") -> Optional[ProjectColumn]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(MAX(display_order), -1) AS max_order FROM project_columns WHERE project_id = ?",
                (project_id,),
            )
            next_order = int(cur.fetchone()["max_order"] or -1) + 1
            inserted = self.insert(
                project_id=project_id,
                column_name=column_name,
                owner_role=owner_role,
                is_auto=0,
                display_order=next_order,
                can_edit=0,
            )
            return inserted[0] if inserted else None
        finally:
            close_connection(conn)

    def delete_project_columns(self, project_id: int) -> None:
        self.clear_project_columns(project_id)


__all__ = ["ProjectColumn", "ProjectColumnRepository"]
