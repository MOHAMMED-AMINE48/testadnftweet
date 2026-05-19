"""
Repository SQLite pour la gestion des Utilisateurs.
Gère l'authentification et la persistence des utilisateurs.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from db_sqlite import get_connection, close_connection


@dataclass
class AppUser:
    """
    Modèle de données pour un Utilisateur de l'application.
    """
    id: int
    email: str
    password_hash: str
    full_name: Optional[str]
    role: str = "BUYER"  # Default role
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "AppUser":
        """Crée une instance AppUser à partir d'une ligne SQLite."""
        return cls(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"] if "role" in row.keys() else "BUYER",
            created_at=row["created_at"]
        )


class UserRepository:
    """
    Repository pour la gestion des utilisateurs en SQLite.
    """

    def __init__(self):
        """Initialise le repository."""
        pass

    def get_user_by_email(self, email: str) -> Optional[AppUser]:
        """
        Récupère un utilisateur par son email.
        
        Args:
            email: L'email de l'utilisateur
        
        Returns:
            L'utilisateur ou None s'il n'existe pas
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, email, password_hash, full_name, role, created_at FROM app_users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            
            close_connection(conn)
            
            if row:
                return AppUser.from_row(row)
            return None
        
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[AppUser]:
        """
        Récupère un utilisateur par son ID.
        
        Args:
            user_id: L'ID de l'utilisateur
        
        Returns:
            L'utilisateur ou None s'il n'existe pas
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, email, password_hash, full_name, role, created_at FROM app_users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            close_connection(conn)
            
            if row:
                return AppUser.from_row(row)
            return None
        
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None
    ) -> Optional[AppUser]:
        """
        Crée un nouvel utilisateur.
        
        Args:
            email: L'email unique de l'utilisateur
            password_hash: Le hash du mot de passe (déjà hashé)
            full_name: Le nom complet de l'utilisateur
        
        Returns:
            L'utilisateur créé ou None en cas d'erreur
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO app_users (email, password_hash, full_name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, password_hash, full_name, now)
            )
            
            conn.commit()
            user_id = cursor.lastrowid
            close_connection(conn)
            
            # Retourner l'utilisateur créé
            return AppUser(
                id=user_id,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                created_at=now
            )
        
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        password_hash: Optional[str] = None
    ) -> Optional[AppUser]:
        """
        Met à jour les informations d'un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur à mettre à jour
            full_name: Le nouveau nom complet (optionnel)
            password_hash: Le nouveau hash du mot de passe (optionnel)
        
        Returns:
            L'utilisateur mis à jour ou None
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            
            if password_hash is not None:
                updates.append("password_hash = ?")
                params.append(password_hash)
            
            if not updates:
                close_connection(conn)
                return self.get_user_by_id(user_id)
            
            params.append(user_id)
            query = f"UPDATE app_users SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, params)
            conn.commit()
            close_connection(conn)
            
            return self.get_user_by_id(user_id)
        
        except Exception as e:
            print(f"Error updating user: {e}")
            return None

    def list_all_users(self) -> list[AppUser]:
        """
        Récupère tous les utilisateurs.
        
        Returns:
            Liste des utilisateurs
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, email, password_hash, full_name, role, created_at FROM app_users")
            rows = cursor.fetchall()
            
            close_connection(conn)
            
            return [AppUser.from_row(row) for row in rows]
        
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def user_exists(self, email: str) -> bool:
        """
        Vérifie si un utilisateur existe.
        
        Args:
            email: L'email à vérifier
        
        Returns:
            True si l'utilisateur existe, False sinon
        """
        return self.get_user_by_email(email) is not None

    def delete_user(self, user_id: int) -> bool:
        """
        Supprime un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur à supprimer
        
        Returns:
            True si suppression réussie, False sinon
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM app_users WHERE id = ?", (user_id,))
            conn.commit()
            close_connection(conn)
            
            return True
        
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """
        Met à jour le rôle d'un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur
            role: Le nouveau rôle (BUYER, CAPACITY_MANAGER, SQD, ADMIN, SUPER_ADMIN)
        
        Returns:
            True si mise à jour réussie, False sinon
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE app_users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()
            close_connection(conn)
            
            return True
        
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
    
    def list_all_users(self) -> list[AppUser]:
        """
        Récupère tous les utilisateurs.
        
        Returns:
            Liste de tous les utilisateurs
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, email, password_hash, full_name, role, created_at FROM app_users ORDER BY email")
            rows = cursor.fetchall()
            
            close_connection(conn)
            
            return [AppUser.from_row(row) for row in rows]
        
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
