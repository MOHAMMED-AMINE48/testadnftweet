"""
Schémas et modèles de données pour CMF.
Définit la structure des données et les validations métier.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


@dataclass
class CMFRecord:
    """
    Représente une ligne du fichier CMF_MASTER.xlsx
    
    Attributes:
        row_id: Identifiant unique de la ligne
        apqp: Code APQP
        partname: Nom du composant
        commodity: Commodity
        new_co: Nouveau C/O
        use_case: Use case
        part_number: Numéro de pièce (peut être vide ou "NEW")
        quantity: Quantité requise
        supplier_name: Nom du fournisseur
        manufacturing_cofor: COFOR de fabrication
        production_location: Localisation de production
        buyer: Acheteur
        purchasing_manager: Responsable achat
        gm: General Manager
        sque: Specialist Quality Engineer
        
        # Données Capacity Manager
        scr: Supply Chain Risk
        link_to_doc_info: Lien vers documentation
        gst_no: Numéro GST
        mix: Ratio de capacité
        capacity_source: Source de capacité (LTOS, GST, FETE, TKO)
        calculated_weekly_capacity: Capacité calculée (parts/week)
        cm_comment: Commentaire Capacity Manager
        
        # Données SQD
        weekly_capacity_to_measure: Capacité à mesurer
        k9_sck: K9 SCK
        cat1_forecasted_date: Date prévue CAT1
        cat2_forecasted_date: Date prévue CAT2
        cat3_forecasted_date: Date prévue CAT3
        cat1_type: Type CAT1
        cat2_type: Type CAT2
        cat3_type: Type CAT3
        weekly_capacity_measured: Capacité mesurée
        estimated_target: Cible estimée
        cat1_evaluation: Évaluation CAT1 (G/O/R)
        cat2_evaluation: Évaluation CAT2 (G/O/R)
        cat3_evaluation: Évaluation CAT3 (G/O/R)
        shared_folder: Lien vers dossier partagé
        sqd_comment: Commentaire SQD
        sque_team: Équipe SQE/SQM
        
        # Métadonnées système
        status: Statut (PRESOURCING, ACTIVE, INACTIVE, PENDING)
        last_updated: Date/heure dernière modification
        updated_by: Utilisateur ayant modifié
    """
    
    # Données Acheteur
    apqp: str = ""
    partname: str = ""
    commodity: str = ""
    new_co: str = ""
    use_case: str = ""
    part_number: str = ""
    quantity: float = 0.0
    supplier_name: str = ""
    manufacturing_cofor: str = ""
    production_location: str = ""
    buyer: str = ""
    purchasing_manager: str = ""
    gm: str = ""
    sque: str = ""
    
    # Données Capacity Manager
    scr: str = ""
    link_to_doc_info: str = ""
    gst_no: str = ""
    mix: float = 1.0
    capacity_source: str = ""
    calculated_weekly_capacity: float = 0.0
    cm_comment: str = ""
    
    # Données SQD
    weekly_capacity_to_measure: float = 0.0
    k9_sck: str = ""
    cat1_forecasted_date: str = ""
    cat2_forecasted_date: str = ""
    cat3_forecasted_date: str = ""
    cat1_type: str = ""
    cat2_type: str = ""
    cat3_type: str = ""
    weekly_capacity_measured: float = 0.0
    estimated_target: str = ""
    cat1_evaluation: str = ""
    cat2_evaluation: str = ""
    cat3_evaluation: str = ""
    shared_folder: str = ""
    sqd_comment: str = ""
    sque_team: str = ""
    
    # Métadonnées
    status: str = "PRESOURCING"
    last_updated: str = ""
    updated_by: str = ""
    row_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le record en dictionnaire"""
        return asdict(self)
    
    def to_series(self) -> Dict[str, Any]:
        """Convertit le record en dictionnaire compatible avec les anciens appels."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CMFRecord":
        """Crée un record à partir d'un dictionnaire"""
        # Filtrer les clés invalides
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def is_presourcing(self) -> bool:
        """Vérifie si le record est en presourcing"""
        return self.status == "PRESOURCING" or not self.part_number or self.part_number == "NEW"
    
    def has_complete_buyer_data(self) -> bool:
        """Vérifie que les données obligatoires de l'Acheteur sont remplies"""
        return bool(self.partname and self.supplier_name and self.quantity > 0)
    
    def has_capacity_info(self) -> bool:
        """Vérifie que les infos de capacité sont présentes"""
        return self.calculated_weekly_capacity > 0 and self.capacity_source


@dataclass
class CapacitySource:
    """
    Représente une source de capacité
    (LTOS, GST, FETE, TKO)
    """
    
    source_name: str  # ex: "LTOS"
    supplier_name: str  # ex: "SUPPLIER_XYZ"
    part_number: str
    weekly_capacity: float  # parties/semaine
    mix_ratio: float = 1.0
    last_updated: str = ""
    data_source_file: str = ""  # fichier source
    
    def calculate_available_capacity(self, mix: float = 1.0) -> float:
        """Calcule la capacité disponible après application du mix"""
        return self.weekly_capacity * mix
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)


@dataclass
class AuditLog:
    """
    Journal d'audit des modifications
    """
    
    timestamp: str
    user: str
    role: str
    action: str  # CREATE, UPDATE, DELETE, IMPORT
    table: str  # CMF, AUDIT_LOGS, etc
    record_id: Optional[int] = None
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)


class CapacityCalculationMethod(str, Enum):
    """Méthodes de calcul de capacité"""
    DIRECT = "DIRECT"  # Utilise dirctement la valeur source
    MIXED = "MIXED"  # Applique le ratio mix
    WEIGHTED = "WEIGHTED"  # Moyenne pondérée de plusieurs sources
    CUSTOM = "CUSTOM"  # Valeur personnalisée


@dataclass
class ValidationResult:
    """Résultat de validation"""
    
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """Ajoute une erreur"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Ajoute un avertissement"""
        self.warnings.append(message)
    
    def get_summary(self) -> str:
        """Retourne un résumé des erreurs/avertissements"""
        lines = []
        if self.errors:
            lines.append("❌ Erreurs:")
            lines.extend([f"  • {e}" for e in self.errors])
        if self.warnings:
            lines.append("⚠️ Avertissements:")
            lines.extend([f"  • {w}" for w in self.warnings])
        return "\n".join(lines)


@dataclass
class ImportResult:
    """Résultat d'un import"""
    
    source_name: str
    total_records: int
    imported_records: int
    skipped_records: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = ""
    imported_by: str = ""
    
    @property
    def success_rate(self) -> float:
        """Taux de succès en pourcentage"""
        if self.total_records == 0:
            return 0.0
        return (self.imported_records / self.total_records) * 100
    
    def get_summary(self) -> str:
        """Résumé de l'import"""
        return (
            f"📥 Import de {self.source_name}\n"
            f"  Total: {self.total_records} | "
            f"Importés: {self.imported_records} | "
            f"Ignorés: {self.skipped_records}\n"
            f"  Taux réussite: {self.success_rate:.1f}%"
        )
