"""
Repository SQLite pour la gestion des Projets/CMF.
Implémente le pattern Repository pour la couche de persistance.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from db_sqlite import get_connection, close_connection


@dataclass
class Project:
    """
    Modèle de données pour un Projet/CMF.
    """
    id: int
    code: str
    name: str
    description: Optional[str]
    capacity_manager_name: str
    buyer_assigned_name: Optional[str]
    sqd_assigned_name: Optional[str]
    supplier_name: Optional[str]
    cmf_status: str
    cmf_schema: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Project":
        """Crée une instance Project à partir d'une ligne SQLite."""
        return cls(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"],
            capacity_manager_name=row["capacity_manager_name"],
            buyer_assigned_name=row["buyer_assigned_name"],
            sqd_assigned_name=row["sqd_assigned_name"],
            supplier_name=row["supplier_name"],
            cmf_status=row["cmf_status"],
            cmf_schema=row["cmf_schema"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


class ProjectRepository:
    """
    Repository pour gérer les projets/CMF en SQLite.
    """

    def get_projects_for_user(self, user_name: str, role: Optional[str] = None) -> List[Project]:
        """
        Retourne les projets pour lesquels l'utilisateur a un rôle.
        
        Args:
            user_name: Nom d'utilisateur
            
        Returns:
            Liste des projets assignés
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            # If the caller indicates a privileged role, return all projects
            role_upper = str(role).strip().upper() if role else None
            if role_upper in ("SUPER_ADMIN", "CAPACITY_MANAGER", "ADMIN"):
                return self.get_all_projects()

            cur.execute("""
                SELECT DISTINCT p.*
                FROM projects p
                JOIN user_project_roles upr ON upr.project_id = p.id
                WHERE upr.user_name = ? AND upr.is_active = 1
                ORDER BY p.name
            """, (user_name,))
            rows = cur.fetchall()
            return [Project.from_row(row) for row in rows]
        finally:
            close_connection(conn)

    def get_all_projects(self) -> List[Project]:
        """
        Retourne tous les projets.
        
        Returns:
            Liste de tous les projets
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects ORDER BY name")
            rows = cur.fetchall()
            return [Project.from_row(row) for row in rows]
        finally:
            close_connection(conn)

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """
        Retourne un projet par son ID.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Le projet, ou None s'il n'existe pas
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cur.fetchone()
            return Project.from_row(row) if row else None
        finally:
            close_connection(conn)

    def get_project_by_code(self, code: str) -> Optional[Project]:
        """
        Retourne un projet par son code.
        
        Args:
            code: Code du projet
            
        Returns:
            Le projet, ou None s'il n'existe pas
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE code = ?", (code,))
            row = cur.fetchone()
            return Project.from_row(row) if row else None
        finally:
            close_connection(conn)

    def create_project(
        self,
        code: str,
        name: str,
        capacity_manager_name: str,
        description: Optional[str] = None,
        buyer_assigned_name: Optional[str] = None,
        sqd_assigned_name: Optional[str] = None,
        supplier_name: Optional[str] = None,
        cmf_status: str = "ACTIVE",
        cmf_schema: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Project:
        """
        Crée un nouveau projet.
        
        Args:
            code: Code unique du projet
            name: Nom du projet
            capacity_manager_name: Nom du Capacity Manager responsable
            description: Description optionnelle
            buyer_assigned_name: Buyer assigné (optionnel)
            sqd_assigned_name: SQD assigné (optionnel)
            supplier_name: Fournisseur (optionnel)
            cmf_status: Statut du CMF (par défaut: ACTIVE)
            cmf_schema: Configuration JSON des colonnes (optionnel)
            created_by: Utilisateur créateur
            
        Returns:
            Le projet créé
            
        Raises:
            ValueError: Si le code existe déjà
        """
        # Vérifier que le code n'existe pas
        if self.get_project_by_code(code):
            raise ValueError(f"Project with code '{code}' already exists")

        conn = get_connection()
        try:
            cur = conn.cursor()
            now = datetime.now().isoformat()
            cur.execute("""
                INSERT INTO projects (
                    code, name, description,
                    capacity_manager_name, buyer_assigned_name, sqd_assigned_name,
                    supplier_name, cmf_status, cmf_schema,
                    created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, name, description,
                capacity_manager_name, buyer_assigned_name, sqd_assigned_name,
                supplier_name, cmf_status, cmf_schema,
                created_by, now, now
            ))
            conn.commit()
            project_id = cur.lastrowid

            from repositories.project_column_repository_sqlite import ProjectColumnRepository

            ProjectColumnRepository().initialize_standard_columns(project_id)

            return Project(
                id=project_id,
                code=code,
                name=name,
                description=description,
                capacity_manager_name=capacity_manager_name,
                buyer_assigned_name=buyer_assigned_name,
                sqd_assigned_name=sqd_assigned_name,
                supplier_name=supplier_name,
                cmf_status=cmf_status,
                cmf_schema=cmf_schema,
                created_by=created_by,
                created_at=now,
                updated_at=now
            )
        finally:
            close_connection(conn)

    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """
        Met à jour un projet.
        
        Args:
            project_id: ID du projet à mettre à jour
            **kwargs: Champs à mettre à jour
            
        Returns:
            Le projet mis à jour, ou None s'il n'existe pas
        """
        # Vérifier que le projet existe
        existing = self.get_project_by_id(project_id)
        if not existing:
            return None

        # Valider et filtrer les champs
        allowed_fields = {
            "name", "description", "capacity_manager_name",
            "buyer_assigned_name", "sqd_assigned_name", "supplier_name",
            "cmf_status", "cmf_schema"
        }
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_data:
            return existing

        update_data["updated_at"] = datetime.now().isoformat()

        # Construire la requête UPDATE
        set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [project_id]

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return self.get_project_by_id(project_id)
        finally:
            close_connection(conn)

    def delete_project(self, project_id: int) -> bool:
        """
        Supprime un projet (suppression logique via ON DELETE CASCADE).
        
        Args:
            project_id: ID du projet à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            close_connection(conn)

    def assign_user_to_project(
        self,
        user_name: str,
        project_id: int,
        role: str,
        assigned_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Assigne un utilisateur à un rôle sur un projet.
        
        Args:
            user_name: Nom d'utilisateur
            project_id: ID du projet
            role: Rôle (BUYER, CAPACITY_MANAGER, SQD, ADMIN)
            assigned_by: Utilisateur qui fait l'assignation
            notes: Notes optionnelles
            
        Returns:
            True si l'assignation a réussi
            
        Raises:
            ValueError: Si le projet n'existe pas
        """
        # Vérifier que le projet existe
        if not self.get_project_by_id(project_id):
            raise ValueError(f"Project with id {project_id} does not exist")

        conn = get_connection()
        try:
            cur = conn.cursor()
            now = datetime.now().isoformat()
            
            # Utiliser INSERT OR REPLACE pour upsert
            cur.execute("""
                INSERT OR REPLACE INTO user_project_roles (
                    user_name, project_id, role, assigned_at, assigned_by, is_active, notes
                ) VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (user_name, project_id, role, now, assigned_by, notes))
            
            conn.commit()
            return True
        finally:
            close_connection(conn)

    def remove_user_from_project(
        self,
        user_name: str,
        project_id: int,
        role: Optional[str] = None
    ) -> bool:
        """
        Retire un utilisateur d'un projet.
        
        Args:
            user_name: Nom d'utilisateur
            project_id: ID du projet
            role: Rôle optionnel (si None, retire tous les rôles)
            
        Returns:
            True si la suppression a réussi
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            if role:
                cur.execute("""
                    UPDATE user_project_roles
                    SET is_active = 0
                    WHERE user_name = ? AND project_id = ? AND role = ?
                """, (user_name, project_id, role))
            else:
                cur.execute("""
                    UPDATE user_project_roles
                    SET is_active = 0
                    WHERE user_name = ? AND project_id = ?
                """, (user_name, project_id))
            
            conn.commit()
            return cur.rowcount > 0
        finally:
            close_connection(conn)

    def get_users_for_project(self, project_id: int, role: Optional[str] = None) -> List[str]:
        """
        Retourne les utilisateurs assignés à un projet.
        
        Args:
            project_id: ID du projet
            role: Filtre optionnel par rôle
            
        Returns:
            Liste des noms d'utilisateurs
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            if role:
                cur.execute("""
                    SELECT DISTINCT user_name
                    FROM user_project_roles
                    WHERE project_id = ? AND role = ? AND is_active = 1
                    ORDER BY user_name
                """, (project_id, role))
            else:
                cur.execute("""
                    SELECT DISTINCT user_name
                    FROM user_project_roles
                    WHERE project_id = ? AND is_active = 1
                    ORDER BY user_name
                """, (project_id,))
            
            rows = cur.fetchall()
            return [row["user_name"] for row in rows]
        finally:
            close_connection(conn)
