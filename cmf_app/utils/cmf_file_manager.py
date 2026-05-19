"""
CMF File Management Utilities
Gère la création et le chargement des fichiers CMF par projet.
"""

from pathlib import Path
from typing import Dict, Optional
import json
import re
import os

from services.excel_service import ExcelService
from utils.cmf_schema_builder import CMFSchema


# ==================== GET BASE DIRECTORY ====================
def get_base_project_directory() -> Path:
    """
    Retourne le répertoire de base pour les projets CMF.
    Construite un chemin absolu vers cmf_app/data/projects
    
    Returns:
        Path au répertoire de base (data/projects)
    """
    # Получить le répertoire de l'application (cmf_app)
    app_dir = Path(__file__).parent.parent  # Remonte de utils/ à cmf_app/
    base_dir = app_dir / "data" / "projects"
    return base_dir


# ==================== CMF FILE PATHS ====================
def get_cmf_directory(project_code: str, base_dir: Optional[Path] = None) -> Path:
    """
    Retourne le répertoire CMF pour un projet.
    
    Args:
        project_code: Code du projet (ex: PRJ001)
        base_dir: Répertoire de base (optionnel, utilise cmf_app/data/projects par défaut)
    
    Returns:
        Path au dossier du CMF
    """
    if base_dir is None:
        base_dir = get_base_project_directory()
    else:
        base_dir = Path(base_dir)
    
    # Nettoyer le project_code
    clean_code = re.sub(r'[^a-zA-Z0-9_-]', '', project_code)
    cmf_dir = base_dir / clean_code
    return cmf_dir


def get_cmf_excel_path(project_code: str, base_dir: Optional[Path] = None) -> Path:
    """
    Retourne le chemin complet du fichier CMF_MASTER.xlsx.
    
    Args:
        project_code: Code du projet
        base_dir: Répertoire de base (optionnel)
    
    Returns:
        Path complète au fichier Excel
    """
    cmf_dir = get_cmf_directory(project_code, base_dir)
    return cmf_dir / "CMF_MASTER.xlsx"


def get_cmf_schema_path(project_code: str, base_dir: Optional[Path] = None) -> Path:
    """
    Retourne le chemin au fichier de schéma JSON.
    
    Args:
        project_code: Code du projet
        base_dir: Répertoire de base
    
    Returns:
        Path au fichier schema.json
    """
    cmf_dir = get_cmf_directory(project_code, base_dir)
    return cmf_dir / "schema.json"


# ==================== CMF FILE CREATION ====================
def create_cmf_file_on_disk(
    project_code: str,
    project_name: str,
    base_dir: Optional[Path] = None,
    cmf_schema: Optional[CMFSchema] = None
) -> str:
    """
    Crée physiquement un fichier CMF pour un projet.
    
    Étapes:
    1. Détermine le chemin fichier
    2. Crée le répertoire s'il n'existe pas
    3. Crée le fichier Excel avec:
       - Colonnes du schema si fourni (schema-driven)
       - Colonnes standard CMF_COLUMNS sinon (backward compatible)
    4. Retourne le chemin complet
    
    Args:
        project_code: Code du projet (ex: PRJ001)
        project_name: Nom du projet (ex: Toyota Parts)
        base_dir: Répertoire de base pour les projets (optionnel)
        cmf_schema: Objet CMFSchema avec configuration de colonnes (optionnel)
                   Si fourni, le fichier Excel sera créé avec ces colonnes exactes.
                   Si None, utilise le comportement std (CMF_COLUMNS).
    
    Returns:
        str: Chemin complet au fichier CMF créé
    
    Raises:
        Exception: Si création échoue
    """
    try:
        # Déterminer le chemin
        cmf_path = get_cmf_excel_path(project_code, base_dir)
        cmf_dir = cmf_path.parent
        
        # Créer le répertoire
        cmf_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer le fichier Excel via ExcelService
        excel_service = ExcelService(str(cmf_path))
        
        # ✅ NEW: Si schema fourni, utiliser la création schema-driven
        if cmf_schema is not None:
            # Convertir CMFSchema en dictionnaire pour la création
            schema_dict = {
                "buyer_columns": cmf_schema.get_all_buyer_columns(),
                "capacity_manager_columns": cmf_schema.get_all_capacity_manager_columns(),
                "sqd_columns": cmf_schema.get_all_sqd_columns(),
            }
            
            # Supprimer le fichier s'il existe déjà (pour le recréer avec le bon schema)
            if cmf_path.exists():
                cmf_path.unlink()
            
            # Créer le ExcelService à nouveau (sans le fichier)
            excel_service = ExcelService.__new__(ExcelService)
            excel_service.file_path = Path(cmf_path)
            
            # Créer le fichier avec le schema
            excel_service.create_cmf_file_with_schema(schema_dict, include_technical=True)
        
        # OLD: _ensure_file_exists() déjà appelé par __init__ de ExcelService
        # qui crée un fichier standard si pas de schema
        
        return str(cmf_path)
    
    except Exception as e:
        raise Exception(f"Failed to create CMF file for {project_code}: {str(e)}")



# ==================== CMF SCHEMA PERSISTENCE ====================
def save_cmf_schema(project_code: str, schema: CMFSchema, base_dir: Optional[Path] = None) -> None:
    """
    Sauvegarde le schéma CMF dans un fichier JSON.
    
    Args:
        project_code: Code du projet
        schema: Objet CMFSchema
        base_dir: Répertoire de base (optionnel)
    
    Raises:
        Exception: Si sauvegarde échoue
    """
    try:
        schema_path = get_cmf_schema_path(project_code, base_dir)
        
        # Créer le répertoire s'il n'existe pas
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire JSON
        with open(schema_path, 'w', encoding='utf-8') as f:
            f.write(schema.to_json())
    
    except Exception as e:
        raise Exception(f"Failed to save CMF schema for {project_code}: {str(e)}")


def load_cmf_schema(project_code: str, base_dir: Optional[Path] = None) -> Optional[CMFSchema]:
    """
    Charge le schéma CMF d'un fichier JSON.
    
    Args:
        project_code: Code du projet
        base_dir: Répertoire de base (optionnel)
    
    Returns:
        CMFSchema object si found, None sinon
    """
    try:
        schema_path = get_cmf_schema_path(project_code, base_dir)
        
        if not schema_path.exists():
            return None
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_json = f.read()
        
        return CMFSchema.from_json(schema_json)
    
    except Exception as e:
        print(f"Error loading schema for {project_code}: {str(e)}")
        return None


# ==================== CMF COLUMN FILTERING ====================
def get_visible_columns_for_role(project_code: str, role: str, base_dir: Optional[Path] = None) -> list:
    """
    Retourne les colonnes visibles pour un rôle spécifique dans un CMF.
    
    Args:
        project_code: Code du projet
        role: Rôle ('BUYER', 'CAPACITY_MANAGER', 'SQD')
        base_dir: Répertoire de base (optionnel)
    
    Returns:
        Liste des noms de colonnes
    """
    schema = load_cmf_schema(project_code, base_dir)
    
    if schema is None:
        # Si pas de schéma, retourner liste vide
        return []
    
    role_upper = role.upper()
    
    if role_upper == 'BUYER':
        return schema.get_all_buyer_columns()
    elif role_upper == 'CAPACITY_MANAGER':
        return schema.get_all_capacity_manager_columns()
    elif role_upper == 'SQD':
        return schema.get_all_sqd_columns()
    else:
        return []


# ==================== VALIDATION ====================
def verify_cmf_file_exists(project_code: str, base_dir: Optional[Path] = None) -> bool:
    """
    Vérifie qu'un fichier CMF existe sur le disque.
    
    Args:
        project_code: Code du projet
        base_dir: Répertoire de base (optionnel)
    
    Returns:
        True si fichier existe, False sinon
    """
    cmf_path = get_cmf_excel_path(project_code, base_dir)
    return cmf_path.exists()
