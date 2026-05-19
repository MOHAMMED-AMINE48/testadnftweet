"""
Helper pour les formulaires de saisie filtrés par colonnes du projet.
Permet de charger la configuration des colonnes et de filtrer les formulaires.
"""

from typing import Any, Dict, List, Optional, Tuple

from repositories.project_column_repository_sqlite import ProjectColumnRepository
from repositories.project_repository_sqlite import ProjectRepository
from services.master_schema import STANDARD_COLUMNS_ORDER
from utils.column_schema_manager import ProjectColumnSchema, AVAILABLE_COLUMNS, get_filtered_columns_for_form


def load_project_column_schema(project_id: int) -> Optional[ProjectColumnSchema]:
    """
    Charge la configuration des colonnes pour un projet.
    
    Args:
        project_id: ID du projet
        
    Returns:
        ProjectColumnSchema ou None si projet non trouvé
    """
    try:
        column_repo = ProjectColumnRepository()
        project_columns = column_repo.get_project_columns(project_id)

        if project_columns:
            buyer_cols = column_repo.get_editable_columns(project_id, "BUYER")
            cm_cols = column_repo.get_editable_columns(project_id, "CAPACITY_MANAGER")
            sqd_cols = column_repo.get_editable_columns(project_id, "SQD")
            buyer_standard = [column for column in buyer_cols if column in STANDARD_COLUMNS_ORDER]
            buyer_custom = [column for column in buyer_cols if column not in STANDARD_COLUMNS_ORDER]
            capacity_manager_standard = [column for column in cm_cols if column in STANDARD_COLUMNS_ORDER]
            capacity_manager_custom = [column for column in cm_cols if column not in STANDARD_COLUMNS_ORDER]
            sqd_standard = [column for column in sqd_cols if column in STANDARD_COLUMNS_ORDER]
            sqd_custom = [column for column in sqd_cols if column not in STANDARD_COLUMNS_ORDER]

            # Keep fixed columns visible to every role via the helper layer.
            return ProjectColumnSchema(
                buyer_standard=buyer_standard,
                buyer_custom=buyer_custom,
                capacity_manager_standard=capacity_manager_standard,
                capacity_manager_custom=capacity_manager_custom,
                sqd_standard=sqd_standard,
                sqd_custom=sqd_custom,
            )

        repo = ProjectRepository()
        project = repo.get_project_by_id(project_id)

        if not project or not project.cmf_schema:
            return ProjectColumnSchema.default()

        return load_project_schema_from_json(project.cmf_schema)
    except Exception:
        return ProjectColumnSchema.default()


def load_project_schema_from_json(cmf_schema_json: Optional[str]) -> ProjectColumnSchema:
    """
    Charge un schéma de projet depuis JSON (supporte les deux formats).
    Utilise la fonction du module column_schema_manager.
    
    Args:
        cmf_schema_json: JSON du schéma
        
    Returns:
        ProjectColumnSchema
    """
    from utils.column_schema_manager import load_project_schema
    return load_project_schema(cmf_schema_json)


def get_form_columns(schema: ProjectColumnSchema, role: str) -> Dict[str, str]:
    """
    Retourne les colonnes à afficher dans un formulaire pour un rôle.
    
    Args:
        schema: Configuration du projet
        role: 'buyer', 'capacity_manager', ou 'sqd'
        
    Returns:
        Dict {column_key: column_label}
    """
    return get_filtered_columns_for_form(schema, role)


def get_form_columns_ordered(schema: ProjectColumnSchema, role: str) -> List[Tuple[str, str]]:
    """
    Retourne les colonnes dans l'ordre pour l'affichage du formulaire.
    
    Args:
        schema: Configuration du projet
        role: 'buyer', 'capacity_manager', ou 'sqd'
        
    Returns:
        Liste [(column_key, column_label), ...]
    """
    form_cols = get_form_columns(schema, role)
    return list(form_cols.items())


def add_project_custom_column(
    project_id: int, 
    role: str, 
    column_key: str, 
    column_label: str
) -> bool:
    """
    Ajoute une colonne personnalisée à un projet ET à la base de données.
    
    Args:
        project_id: ID du projet
        role: 'buyer', 'capacity_manager', ou 'sqd'
        column_key: Clé interne (ex: "super_mix")
        column_label: Label pour affichage
        
    Returns:
        True si succès
    """
    try:
        column_repo = ProjectColumnRepository()
        del column_label
        return column_repo.add_custom_column(project_id, column_key, role) is not None
    except Exception as e:
        print(f"❌ Error adding custom column: {str(e)}")
        return False


def validate_form_data(form_data: Dict[str, Any], schema: ProjectColumnSchema, role: str) -> Tuple[bool, List[str]]:
    """
    Valide que les données du formulaire ne contiennent que des colonnes autorisées.
    
    Args:
        form_data: Dictionnaire des données du formulaire
        schema: Configuration du projet
        role: 'buyer', 'capacity_manager', ou 'sqd'
        
    Returns:
        (is_valid, list_of_invalid_columns)
    """
    allowed_cols = schema.get_columns_for_role(role)
    invalid_cols = [key for key in form_data.keys() if key not in allowed_cols]
    
    return len(invalid_cols) == 0, invalid_cols
