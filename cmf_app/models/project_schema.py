"""
Schémas et modèles pour gestion multi-projets.
Définit les entités Project et UserProjectRole pour la gouvernance multi-projets.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path


@dataclass
class Project:
    """
    Représente un CMF (Capacity Management File / Projet Fournisseur) dans la plateforme.
    
    Attributes:
        project_id: Identifiant unique du CMF (ex: PRJ_001)
        project_code: Code du CMF (ex: "TOYOTA_PARTS")
        project_name: Nom lisible (ex: "Toyota Parts - Akatsuki Motors")
        description: Description du projet
        supplier_name: Nom du fournisseur (ex: "Akatsuki Motors")
        initial_capacity: Capacité initiale (ex: 500 parts/week)
        buyer_assigned: Acheteur assigné au CMF
        sqd_assigned: SQD assigné au CMF (Quality Manager)
        cmf_file_path: Chemin vers CMF_MASTER.xlsx du CMF
        cmf_status: Status du CMF (ACTIVE, PAUSED, ARCHIVED)
        cmf_schema: Configuration JSON des colonnes du CMF (optionnel)
        created_by: Utilisateur créateur (Capacity Manager)
        created_at: Date de création
        is_active: CMF actif ou archivé (soft delete)
    """
    
    project_id: str  # Identifiant unique (PRJ_001, PRJ_002, etc)
    project_code: str  # Code unique court (ex: TOYOTA_PARTS)
    project_name: str  # Nom lisible
    capacity_manager_name: str = ""  # Username du Capacity Manager assigné
    supplier_name: str = ""  # Nom du fournisseur
    buyer_assigned: str = ""  # Username du Buyer assigné
    sqd_assigned: str = ""  # Username du SQD assigné
    description: str = ""  # Notes additionnelles
    cmf_file_path: str = ""  # Chemin CMF
    cmf_status: str = "ACTIVE"  # ACTIVE, PAUSED, ARCHIVED
    cmf_schema: str = ""  # Configuration JSON des colonnes (CMFSchema.to_json())
    created_by: str = ""  # Capacity Manager qui a créé
    created_at: str = ""  # Format ISO 8601
    is_active: bool = True  # Soft delete flag
    
    def __post_init__(self):
        """Initialise les valeurs par défaut à la création"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.cmf_file_path:
            # Génère un chemin par défaut: data/projects/PRJ_XXX/CMF_MASTER.xlsx
            self.cmf_file_path = f"data/projects/{self.project_id}/CMF_MASTER.xlsx"
    
    def get_cmf_file_path(self) -> Path:
        """Retourne le chemin CMF en tant que Path object"""
        return Path(self.cmf_file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Crée une instance à partir d'un dictionnaire"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class UserProjectRole:
    """
    Représente l'affectation d'un utilisateur à un rôle sur un projet.
    Clé composite: (user_id, project_id) -> role
    
    Attributes:
        user_id: Identifiant utilisateur
        project_id: Identifiant projet
        role: Rôle sur ce projet (BUYER, CAPACITY_MANAGER, SQD, ADMIN)
        assigned_at: Date d'affectation
        assigned_by: Administrateur ayant fait l'affectation
        is_active: Affectation active ou archivée
    """
    
    user_id: str
    project_id: str
    role: str  # BUYER, CAPACITY_MANAGER, SQD, ADMIN
    assigned_at: str = ""  # Format ISO 8601
    assigned_by: str = ""
    is_active: bool = True
    notes: str = ""  # Notes libres (ex: "Temporaire jusqu'au Q3 2026")
    
    def __post_init__(self):
        """Initialise les valeurs par défaut"""
        if not self.assigned_at:
            self.assigned_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProjectRole":
        """Crée une instance à partir d'un dictionnaire"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class ProjectContext:
    """
    Représente le contexte d'exécution actuel pour un utilisateur.
    Stocké dans st.session_state.
    
    Attributes:
        user_id: Utilisateur connecté
        selected_project: Projet actuellement sélectionné
        user_role: Rôle de l'utilisateur sur ce projet
        available_projects: Projets auxquels l'utilisateur a accès
    """
    
    user_id: str
    selected_project: Optional[Project] = None
    user_role: Optional[str] = None  # Role sur le projet sélectionné
    available_projects: List[Project] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Vérifie que le contexte est valide (projet sélectionné)"""
        return self.selected_project is not None and self.user_role is not None
    
    @property
    def can_access_project(self, project_id: str) -> bool:
        """Vérifie si l'utilisateur peut accéder à un projet"""
        return any(p.project_id == project_id for p in self.available_projects)


class ProjectStatus(str, Enum):
    """Statuts possibles d'un projet"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    PENDING = "PENDING"
    INACTIVE = "INACTIVE"
