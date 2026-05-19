"""
Service de gestion du contexte projet (ProjectContextService)
Gère la sélection du projet actuel et le contrôle d'accès par utilisateur
"""

from typing import Optional, List
from datetime import datetime

from models.project_schema import Project, UserProjectRole, ProjectContext
from services.project_repository import JSONProjectRepository, JSONUserProjectRepository


class ProjectContextService:
    """
    Service pour gérer le contexte de projet actuel.
    Responsabilités:
    - Sélectionner le projet actif
    - Vérifier l'accès utilisateur au projet
    - Fournir l'ExcelService pour le CMF actif
    - Audit des changements de projet
    """
    
    def __init__(self):
        """Initialise le service"""
        self.project_repo = JSONProjectRepository()
        self.user_repo = JSONUserProjectRepository()
    
    def get_available_projects_for_user(self, user_id: str) -> List[Project]:
        """
        Récupère tous les projets accessibles par un utilisateur.
        
        Args:
            user_id: Identifiant utilisateur
        
        Returns:
            Liste des projets accessibles
        """
        return self.user_repo.get_user_projects(user_id)
    
    def get_user_role_on_project(self, user_id: str, project_id: str) -> Optional[str]:
        """
        Récupère le rôle de l'utilisateur sur un projet.
        
        Args:
            user_id: Identifiant utilisateur
            project_id: Identifiant projet
        
        Returns:
            Rôle (BUYER, CAPACITY_MANAGER, SQD, ADMIN) ou None
        """
        return self.user_repo.get_user_role_on_project(user_id, project_id)
    
    def can_access_project(self, user_id: str, project_id: str) -> bool:
        """
        Vérifie qu'un utilisateur peut accéder à un projet.
        
        Args:
            user_id: Identifiant utilisateur
            project_id: Identifiant projet
        
        Returns:
            True si l'utilisateur a accès, False sinon
        """
        role = self.get_user_role_on_project(user_id, project_id)
        return role is not None
    
    def select_project(self, user_id: str, project_id: str, user_role: str = None) -> tuple[bool, Optional[ProjectContext], str]:
        """
        Sélectionne le projet actif pour un utilisateur.
        Effectue les vérifications d'accès (⚠️ ignorées pour les Admins).
        
        Args:
            user_id: Identifiant utilisateur
            project_id: Identifiant projet à sélectionner
            user_role: Rôle utilisateur (pour vérification Admin)
        
        Returns:
            (success: bool, context: ProjectContext, message: str)
        """
        # Récupère le projet
        project = self.project_repo.get_project_by_id(project_id)
        if not project or not project.is_active:
            return (
                False,
                None,
                f"Project {project_id} not found or inactive"
            )
        
        # ✅ Admins: accès sans restriction
        if user_role == "ADMIN":
            # Admin peut accéder à TOUS les projets
            available_projects = self.project_repo.get_all_projects()
            role = "ADMIN"
        else:
            # ✅ Utilisateurs normaux: vérification d'accès
            if not self.can_access_project(user_id, project_id):
                return (
                    False,
                    None,
                    f"Access denied: User {user_id} cannot access project {project_id}"
                )
            
            available_projects = self.get_available_projects_for_user(user_id)
            role = self.get_user_role_on_project(user_id, project_id)
        
        # Crée le contexte avec projet sélectionné
        context = ProjectContext(
            user_id=user_id,
            selected_project=project,
            user_role=role,
            available_projects=available_projects
        )
        
        return (True, context, f"Project {project.project_name} selected successfully")
    
    def initialize_user_context(self, user_id: str, user_role: str = None) -> tuple[bool, Optional[ProjectContext], str]:
        """
        Initialise le contexte pour un utilisateur à la connexion.
        ⚠️ N'effectue JAMAIS de blocage – tous les utilisateurs peuvent entrer.
        
        Args:
            user_id: Identifiant utilisateur
            user_role: Rôle utilisateur pour déterminer accès Admin
        
        Returns:
            (success: bool, context: ProjectContext, message: str)
            - success est TOUJOURS True (pas de blocage)
            - context contient les projets disponibles
            - message explicite sur l'état
        """
        # Déterminer les projets accessibles
        if user_role == "ADMIN":
            # Admin accède à TOUS les projets sans restriction
            available_projects = self.project_repo.get_all_projects()
            message = f"Admin user {user_id}: Full access to all {len(available_projects)} projects"
        else:
            # Utilisateur normal: projets affectés uniquement
            available_projects = self.get_available_projects_for_user(user_id)
            if not available_projects:
                message = f"User {user_id}: No projects assigned (can request access or contact admin)"
            else:
                message = f"User {user_id}: Access to {len(available_projects)} project(s)"
        
        # Crée le contexte SANS projet sélectionné (sélection optionnelle)
        context = ProjectContext(
            user_id=user_id,
            available_projects=available_projects,
            selected_project=None,  # Pas de sélection forcée
            user_role=user_role
        )
        
        # ✅ Retours TOUJOURS True – pas de blocage
        return (True, context, message)
    
    def switch_project(self, current_context: ProjectContext, new_project_id: str):
        """
        Bascule vers un autre projet.
        
        Args:
            current_context: Contexte actuel
            new_project_id: ID du nouveau projet
        
        Returns:
            (success: bool, new_context: ProjectContext, message: str)
        """
        # Vérifie que le projet est dans les projets accessibles
        if not any(p.project_id == new_project_id for p in current_context.available_projects):
            return (
                False,
                current_context,
                f"Project {new_project_id} not in available projects"
            )
        
        # Sélectionne le nouveau projet
        return self.select_project(current_context.user_id, new_project_id)
    
    def get_cmf_file_path(self, project_id: str) -> Optional[str]:
        """
        Récupère le chemin du fichier CMF pour un projet.
        
        Args:
            project_id: Identifiant projet
        
        Returns:
            Chemin du fichier CMF ou None
        """
        project = self.project_repo.get_project_by_id(project_id)
        if project:
            return project.cmf_file_path
        return None
    
    def create_project(self, project_code: str, project_name: str, created_by: str, description: str = "") -> tuple[bool, Optional[Project], str]:
        """
        Crée un nouveau projet.
        
        Args:
            project_code: Code du projet unique
            project_name: Nom du projet
            created_by: Utilisateur créateur
            description: Description optionnelle
        
        Returns:
            (success: bool, project: Project, message: str)
        """
        # Génère un ID unique
        existing_projects = self.project_repo.get_all_projects()
        project_number = len(existing_projects) + 1
        project_id = f"PRJ_{project_number:03d}"
        
        # Crée le projet
        project = Project(
            project_id=project_id,
            project_code=project_code,
            project_name=project_name,
            description=description,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        if self.project_repo.create_project(project):
            return (True, project, f"Project {project_id} created successfully")
        else:
            return (False, None, f"Failed to create project {project_id}")
    
    def assign_user_to_project(self, user_id: str, project_id: str, role: str, assigned_by: str) -> tuple[bool, str]:
        """
        Affecte un utilisateur à un rôle sur un projet.
        
        Args:
            user_id: Identifiant utilisateur
            project_id: Identifiant projet
            role: Rôle (BUYER, CAPACITY_MANAGER, SQD, ADMIN)
            assigned_by: Administrateur effectuant l'affectation
        
        Returns:
            (success: bool, message: str)
        """
        if not self.project_repo.get_project_by_id(project_id):
            return (False, f"Project {project_id} not found")
        
        success = self.user_repo.assign_user_to_project(
            user_id=user_id,
            project_id=project_id,
            role=role,
            assigned_by=assigned_by
        )
        
        if success:
            return (True, f"User {user_id} assigned role {role} on project {project_id}")
        else:
            return (False, f"Failed to assign user to project")


# Singleton pour utilisation facile
_context_service = None

def get_project_context_service() -> ProjectContextService:
    """Récupère l'instance singleton du service de contexte"""
    global _context_service
    if _context_service is None:
        _context_service = ProjectContextService()
    return _context_service
