"""
Gestion des schémas CMF - Définition et construction de schémas de colonnes.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any
import json


@dataclass
class CMFSchema:
    """
    Représente le schéma de colonnes d'un CMF.
    Définit quelles colonnes sont disponibles pour chaque rôle.
    """
    
    buyer_standard: List[str] = field(default_factory=list)  # Colonnes standard Buyer sélectionnées
    buyer_custom: List[str] = field(default_factory=list)  # Colonnes custom Buyer
    
    capacity_manager_standard: List[str] = field(default_factory=list)  # Colonnes standard CM sélectionnées
    capacity_manager_custom: List[str] = field(default_factory=list)  # Colonnes custom CM
    
    sqd_standard: List[str] = field(default_factory=list)  # Colonnes standard SQD sélectionnées
    sqd_custom: List[str] = field(default_factory=list)  # Colonnes custom SQD
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le schéma en dictionnaire"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convertit le schéma en JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CMFSchema":
        """Crée un schéma à partir d'un dictionnaire"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "CMFSchema":
        """Crée un schéma à partir d'une chaîne JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_all_buyer_columns(self) -> List[str]:
        """Retourne toutes les colonnes Buyer (standard + custom)"""
        return self.buyer_standard + self.buyer_custom
    
    def get_all_capacity_manager_columns(self) -> List[str]:
        """Retourne toutes les colonnes Capacity Manager (standard + custom)"""
        return self.capacity_manager_standard + self.capacity_manager_custom
    
    def get_all_sqd_columns(self) -> List[str]:
        """Retourne toutes les colonnes SQD (standard + custom)"""
        return self.sqd_standard + self.sqd_custom
    
    def get_all_columns(self) -> Dict[str, List[str]]:
        """Retourne toutes les colonnes par rôle"""
        return {
            "buyer": self.get_all_buyer_columns(),
            "capacity_manager": self.get_all_capacity_manager_columns(),
            "sqd": self.get_all_sqd_columns(),
        }


def build_cmf_schema_from_form(
    buyer_standard: List[str] = None,
    buyer_custom: str = "",
    capacity_manager_standard: List[str] = None,
    capacity_manager_custom: str = "",
    sqd_standard: List[str] = None,
    sqd_custom: str = "",
) -> CMFSchema:
    """
    Construit un schéma CMF à partir des données du formulaire.
    
    Args:
        buyer_standard: Colonnes standard Buyer sélectionnées
        buyer_custom: Colonnes custom Buyer (chaîne séparée par virgules)
        capacity_manager_standard: Colonnes standard CM sélectionnées
        capacity_manager_custom: Colonnes custom CM (chaîne séparée par virgules)
        sqd_standard: Colonnes standard SQD sélectionnées
        sqd_custom: Colonnes custom SQD (chaîne séparée par virgules)
    
    Returns:
        CMFSchema construit
    """
    
    # Traiter les colonnes custom (nettoyer et splitter)
    def parse_custom_columns(custom_str: str) -> List[str]:
        if not custom_str:
            return []
        cols = [col.strip() for col in custom_str.split(",")]
        cols = [col for col in cols if col]  # Filtrer les vides
        return cols
    
    schema = CMFSchema(
        buyer_standard=buyer_standard or [],
        buyer_custom=parse_custom_columns(buyer_custom),
        capacity_manager_standard=capacity_manager_standard or [],
        capacity_manager_custom=parse_custom_columns(capacity_manager_custom),
        sqd_standard=sqd_standard or [],
        sqd_custom=parse_custom_columns(sqd_custom),
    )
    
    return schema
