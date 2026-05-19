"""
Repositories pour gestion multi-projets
Gère les données Project et UserProjectRole
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from models.project_schema import Project, UserProjectRole


def get_config_directory() -> Path:
    """
    Retourne le répertoire de configuration pour les projets.
    Utilise un chemin absolu vers cmf_app/data/projects
    
    Returns:
        Path au répertoire data/projects
    """
    # Find the cmf_app directory - services module is in cmf_app/services
    services_dir = Path(__file__).parent  # cmf_app/services
    app_dir = services_dir.parent  # cmf_app
    config_dir = app_dir / "data" / "projects"
    return config_dir


class IProjectRepository(ABC):
    """Interface pour repository de projets"""
    
    @abstractmethod
    def get_all_projects(self) -> List[Project]:
        """Récupère tous les projets actifs"""
        pass
    
    @abstractmethod
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Récupère un projet par ID"""
        pass
    
    @abstractmethod
    def create_project(self, project: Project) -> bool:
        """Crée un nouveau projet"""
        pass
    
    @abstractmethod
    def update_project(self, project: Project) -> bool:
        """Met à jour un projet"""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Archive un projet (soft delete)"""
        pass


class IUserProjectRepository(ABC):
    """Interface pour repository d'affectations utilisateur-projet"""
    
    @abstractmethod
    def get_user_projects(self, user_id: str) -> List[Project]:
        """Récupère tous les projets d'un utilisateur"""
        pass
    
    @abstractmethod
    def get_user_role_on_project(self, user_id: str, project_id: str) -> Optional[str]:
        """Récupère le rôle d'un utilisateur sur un projet"""
        pass
    
    @abstractmethod
    def assign_user_to_project(self, user_id: str, project_id: str, role: str) -> bool:
        """Affecte un utilisateur à un rôle sur un projet"""
        pass
    
    @abstractmethod
    def remove_user_from_project(self, user_id: str, project_id: str) -> bool:
        """Retire un utilisateur d'un projet"""
        pass
    
    @abstractmethod
    def get_project_users(self, project_id: str) -> List[UserProjectRole]:
        """Récupère tous les utilisateurs affectés à un projet"""
        pass


class JSONProjectRepository(IProjectRepository):
    """
    Implémentation JSON pour repository de projets.
    Stocke les projets dans data/projects/projects.json
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialise le repository JSON.
        
        Args:
            config_dir: Répertoire pour stocker projects.json (optionnel, utilise cmf_app/data/projects par défaut)
        """
        if config_dir is None:
            self.config_dir = get_config_directory()
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / "projects.json"
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """Crée le fichier projects.json s'il n'existe pas"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"projects": []}, f, indent=2, ensure_ascii=False)
    
    def _load_data(self) -> Dict[str, Any]:
        """Charge les données depuis le fichier JSON"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading projects: {e}")
            return {"projects": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """Sauvegarde les données dans le fichier JSON"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving projects: {e}")
    
    def get_all_projects(self) -> List[Project]:
        """Récupère tous les projets actifs"""
        data = self._load_data()
        projects = []
        for proj_dict in data.get("projects", []):
            if proj_dict.get("is_active", True):
                projects.append(Project.from_dict(proj_dict))
        return sorted(projects, key=lambda p: p.created_at, reverse=True)
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Récupère un projet par ID"""
        data = self._load_data()
        for proj_dict in data.get("projects", []):
            if proj_dict.get("project_id") == project_id:
                return Project.from_dict(proj_dict)
        return None
    
    def create_project(self, project: Project) -> bool:
        """Crée un nouveau projet"""
        if self.get_project_by_id(project.project_id):
            return False  # Project already exists
        
        data = self._load_data()
        project.created_at = datetime.now().isoformat()
        data["projects"].append(project.to_dict())
        self._save_data(data)
        
        # Crée le répertoire du projet
        project_dir = self.config_dir / project.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        return True
    
    def update_project(self, project: Project) -> bool:
        """Met à jour un projet"""
        data = self._load_data()
        for i, proj_dict in enumerate(data.get("projects", [])):
            if proj_dict.get("project_id") == project.project_id:
                data["projects"][i] = project.to_dict()
                self._save_data(data)
                return True
        return False
    
    def delete_project(self, project_id: str) -> bool:
        """Archive un projet (soft delete)"""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        project.is_active = False
        return self.update_project(project)


class JSONUserProjectRepository(IUserProjectRepository):
    """
    Implémentation JSON pour affectations utilisateur-projet.
    Stocke dans data/projects/user_assignments.json
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialise le repository.
        
        Args:
            config_dir: Répertoire pour stocker user_assignments.json (optionnel, utilise cmf_app/data/projects par défaut)
        """
        if config_dir is None:
            self.config_dir = get_config_directory()
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / "user_assignments.json"
        self._project_repo = JSONProjectRepository(str(self.config_dir) if config_dir else None)
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """Crée le fichier user_assignments.json s'il n'existe pas"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"assignments": []}, f, indent=2, ensure_ascii=False)
    
    def _load_data(self) -> Dict[str, Any]:
        """Charge les affectations"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading assignments: {e}")
            return {"assignments": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """Sauvegarde les affectations"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving assignments: {e}")
    
    def get_user_projects(self, user_id: str) -> List[Project]:
        """Récupère tous les projets d'un utilisateur"""
        data = self._load_data()
        project_ids = set()
        
        for assignment in data.get("assignments", []):
            if assignment.get("user_id") == user_id and assignment.get("is_active", True):
                project_ids.add(assignment.get("project_id"))
        
        projects = []
        for project_id in project_ids:
            project = self._project_repo.get_project_by_id(project_id)
            if project and project.is_active:
                projects.append(project)
        
        return sorted(projects, key=lambda p: p.project_name)
    
    def get_user_role_on_project(self, user_id: str, project_id: str) -> Optional[str]:
        """Récupère le rôle d'un utilisateur sur un projet"""
        data = self._load_data()
        
        for assignment in data.get("assignments", []):
            if (assignment.get("user_id") == user_id and 
                assignment.get("project_id") == project_id and
                assignment.get("is_active", True)):
                return assignment.get("role")
        
        return None
    
    def assign_user_to_project(self, user_id: str, project_id: str, role: str, assigned_by: str = "") -> bool:
        """Affecte un utilisateur à un rôle sur un projet"""
        # Vérifie que le projet existe
        if not self._project_repo.get_project_by_id(project_id):
            return False
        
        # Si affectation existe, met à jour
        data = self._load_data()
        for assignment in data.get("assignments", []):
            if (assignment.get("user_id") == user_id and 
                assignment.get("project_id") == project_id):
                assignment["role"] = role
                assignment["is_active"] = True
                self._save_data(data)
                return True
        
        # Crée nouvelle affectation
        new_assignment = UserProjectRole(
            user_id=user_id,
            project_id=project_id,
            role=role,
            assigned_by=assigned_by
        )
        data["assignments"].append(new_assignment.to_dict())
        self._save_data(data)
        return True
    
    def remove_user_from_project(self, user_id: str, project_id: str) -> bool:
        """Retire un utilisateur d'un projet (soft delete)"""
        data = self._load_data()
        
        for assignment in data.get("assignments", []):
            if (assignment.get("user_id") == user_id and 
                assignment.get("project_id") == project_id):
                assignment["is_active"] = False
                self._save_data(data)
                return True
        
        return False
    
    def get_project_users(self, project_id: str) -> List[UserProjectRole]:
        """Récupère tous les utilisateurs affectés à un projet"""
        data = self._load_data()
        users = []
        
        for assignment in data.get("assignments", []):
            if (assignment.get("project_id") == project_id and 
                assignment.get("is_active", True)):
                users.append(UserProjectRole.from_dict(assignment))
        
        return sorted(users, key=lambda u: (u.user_id, u.role))


class RepositoryFactory:
    """
    Factory pattern pour créer les repositories.
    Permet de changer les implémentations (JSON vs SQL) sans modifier le code client.
    """
    
    @staticmethod
    def create_project_repository(repo_type: str = "json", config_dir: str = "data/projects") -> IProjectRepository:
        """
        Crée un repository de projets.
        
        Args:
            repo_type: Type de repository ("json" ou "sql")
            config_dir: Répertoire de configuration (pour JSON)
            
        Returns:
            Instance d'IProjectRepository
        """
        if repo_type.lower() == "json":
            return JSONProjectRepository(config_dir)
        elif repo_type.lower() == "sql":
            # À implémenter pour migration SQL
            raise NotImplementedError("SQL repository not yet implemented")
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")
    
    @staticmethod
    def create_user_repository(repo_type: str = "json", config_dir: str = "data/projects") -> IUserProjectRepository:
        """
        Crée un repository d'affectations utilisateur-projet.
        
        Args:
            repo_type: Type de repository ("json" ou "sql")
            config_dir: Répertoire de configuration (pour JSON)
            
        Returns:
            Instance d'IUserProjectRepository
        """
        if repo_type.lower() == "json":
            return JSONUserProjectRepository(config_dir)
        elif repo_type.lower() == "sql":
            # À implémenter pour migration SQL
            raise NotImplementedError("SQL repository not yet implemented")
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")
