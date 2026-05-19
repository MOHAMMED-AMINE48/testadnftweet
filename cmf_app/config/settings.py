"""
Configuration centralisée pour l'application CMF.
Gère les paramètres, les constantes et les chemins.
"""

import os
from pathlib import Path
from enum import Enum

# Chemins définis
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

# Créer les répertoires s'ils n'existent pas
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Base de données SQLite
DATABASE_PATH = DATA_DIR / "cmf.db"

# Logs
LOG_FILE = LOG_DIR / "cmf_audit.log"

# ==================== RÔLES UTILISATEURS ====================
class UserRole(str, Enum):
    """Énumération des rôles utilisateurs"""
    BUYER = "BUYER"
    CAPACITY_MANAGER = "CAPACITY_MANAGER"
    SQD = "SQD"
    ADMIN = "ADMIN"


# ==================== COLONNES CMF ====================
CMF_COLUMNS = {
    # Données saisies par l'Acheteur
    "APQP": str,
    "Partname": str,
    "Commodity": str,
    "NewCO": str,
    "UseCase": str,
    "PartNumber": str,
    "Quantity": float,
    "SupplierName": str,
    "ManufacturingCOFOR": str,
    "ProductionLocation": str,
    "Buyer": str,
    "PurchasingManager": str,
    "GM": str,
    "SQE": str,
    
    # Données saisies par le Capacity Manager
    "SCR": str,
    "LinkToDocInfo": str,
    "GSTNo": str,
    "Mix": float,
    "CapacitySource": str,  # LTOS, GST, FETE, TKO, ou vide
    "CalculatedWeeklyCapacity": float,
    "CMComment": str,
    
    # Données saisies par SQD
    "WeeklyCapacityToMeasure": float,
    "K9SCK": str,
    "CAT1ForecastedDate": str,
    "CAT2ForecastedDate": str,
    "CAT3ForecastedDate": str,
    "CAT1Type": str,
    "CAT2Type": str,
    "CAT3Type": str,
    "WeeklyCapacityMeasured": float,
    "EstimatedTarget": str,
    "CAT1Evaluation": str,
    "CAT2Evaluation": str,
    "CAT3Evaluation": str,
    "SharedFolder": str,
    "SQDComment": str,
    "SQETeam": str,
    
    # Métadonnées système
    "Status": str,  # PRESOURCING, ACTIVE, INACTIVE
    "LastUpdated": str,
    "UpdatedBy": str,
}

# ==================== PERMISSIONS PAR RÔLE ====================
ROLE_PERMISSIONS = {
    UserRole.BUYER: {
        "read": list(CMF_COLUMNS.keys()),
        "write": [
            "APQP", "Partname", "Commodity", "NewCO", "UseCase", "PartNumber",
            "Quantity", "SupplierName", "ManufacturingCOFOR", "ProductionLocation",
            "Buyer", "PurchasingManager", "GM", "SQE"
        ],
    },
    UserRole.CAPACITY_MANAGER: {
        "read": list(CMF_COLUMNS.keys()),
        "write": [
            "SCR", "LinkToDocInfo", "GSTNo", "Mix", "CapacitySource",
            "CalculatedWeeklyCapacity", "CMComment"
        ],
    },
    UserRole.SQD: {
        "read": list(CMF_COLUMNS.keys()),
        "write": [
            "WeeklyCapacityToMeasure", "K9SCK", "CAT1ForecastedDate",
            "CAT2ForecastedDate", "CAT3ForecastedDate", "CAT1Type", "CAT2Type",
            "CAT3Type", "WeeklyCapacityMeasured", "EstimatedTarget",
            "CAT1Evaluation", "CAT2Evaluation", "CAT3Evaluation",
            "SharedFolder", "SQDComment", "SQETeam"
        ],
    },
    UserRole.ADMIN: {
        "read": list(CMF_COLUMNS.keys()),
        "write": list(CMF_COLUMNS.keys()),
    },
}

# ==================== SOURCES DE CAPACITÉ ====================
CAPACITY_SOURCES = ["LTOS", "GST", "FETE", "TKO"]

# ==================== STATUTS ====================
class RecordStatus(str, Enum):
    """Statuts possibles d'une ligne CMF"""
    PRESOURCING = "PRESOURCING"  # Aucune capacité trouvée
    ACTIVE = "ACTIVE"  # Capacité trouvée et calculée
    INACTIVE = "INACTIVE"  # Désactivée manuellement
    PENDING = "PENDING"  # En attente de validation

# ==================== CONFIGURATION STREAMLIT ====================
STREAMLIT_CONFIG = {
    "page_title": "CMF - Capacity Management",
    "page_icon": "",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# ==================== VALIDATIONS ====================
VALIDATION_RULES = {
    "min_quantity": 0.01,
    "min_capacity": 0.01,
    "max_mix_ratio": 1.0,
    "min_mix_ratio": 0.0,
}

# ==================== MESSAGES ====================
MESSAGES = {
    "success": " Opération réussie",
    "error": " Erreur détectée",
    "warning": " Attention",
    "info": " Information",
    "unsupported_operation": "Cette opération n'est pas autorisée pour votre rôle.",
    "data_saved": "Les données ont été sauvegardées avec succès.",
    "presourcing": " En presourcing - Aucune capacité trouvée pour ce partenaire.",
}
