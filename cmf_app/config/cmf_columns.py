"""
Colonnes standards pour chaque rôle CMF (Buyer, Capacity Manager, SQD).
Utilisées pour la configuration flexible des schémas CMF.
"""

from typing import Dict, List

# ==================== COLONNES BUYER ====================
BUYER_STANDARD_COLUMNS = {
    "apqp": "APQP Code",
    "partname": "Part Name",
    "commodity": "Commodity",
    "new_co": "New C/O",
    "use_case": "Use Case",
    "part_number": "Part Number",
    "quantity": "Quantity",
    "supplier_name": "Supplier Name",
    "manufacturing_cofor": "Manufacturing COFOR",
    "production_location": "Production Location",
    "buyer": "Buyer",
    "purchasing_manager": "Purchasing Manager",
    "gm": "General Manager",
    "sque": "SQE/SQM",
}

# ==================== COLONNES CAPACITY MANAGER ====================
CAPACITY_MANAGER_STANDARD_COLUMNS = {
    "scr": "Supply Chain Risk",
    "link_to_doc_info": "Link to DocInfo",
    "gst_no": "GST No.",
    "mix": "Mix Ratio",
    "capacity_source": "Capacity Source",
    "calculated_weekly_capacity": "Calculated Weekly Capacity",
    "cm_comment": "CM Comments",
}

# ==================== COLONNES SQD ====================
SQD_STANDARD_COLUMNS = {
    "weekly_capacity_to_measure": "Capacity to Measure",
    "k9_sck": "K9 SCK",
    "cat1_forecasted_date": "CAT1 Forecasted Date",
    "cat2_forecasted_date": "CAT2 Forecasted Date",
    "cat3_forecasted_date": "CAT3 Forecasted Date",
    "cat1_type": "CAT1 Type",
    "cat2_type": "CAT2 Type",
    "cat3_type": "CAT3 Type",
    "weekly_capacity_measured": "Weekly Capacity Measured",
    "estimated_target": "Estimated Target",
    "cat1_evaluation": "CAT1 Evaluation",
    "cat2_evaluation": "CAT2 Evaluation",
    "cat3_evaluation": "CAT3 Evaluation",
    "shared_folder": "Link to Sharepoint",
    "sqd_comment": "Assessment Comments",
    "sque_team": "SQE Team",
}

# ==================== DEFAULTS SÉLECTIONNÉS ====================
# Colonnes sélectionnées par défaut pour chaque rôle
BUYER_DEFAULT_COLUMNS = [
    "partname",
    "part_number",
    "quantity",
    "supplier_name",
    "buyer",
]

CAPACITY_MANAGER_DEFAULT_COLUMNS = [
    "capacity_source",
    "calculated_weekly_capacity",
    "mix",
]

SQD_DEFAULT_COLUMNS = [
    "weekly_capacity_to_measure",
    "weekly_capacity_measured",
    "cat1_evaluation",
    "cat2_evaluation",
    "cat3_evaluation",
]

# ==================== HELPER: ALL COLUMNS BY ROLE ====================
def get_all_role_columns() -> Dict[str, Dict[str, str]]:
    """Retourne dictionnaire avec toutes les colonnes par rôle"""
    return {
        "buyer": BUYER_STANDARD_COLUMNS,
        "capacity_manager": CAPACITY_MANAGER_STANDARD_COLUMNS,
        "sqd": SQD_STANDARD_COLUMNS,
    }

def get_default_columns() -> Dict[str, List[str]]:
    """Retourne colonnes par défaut par rôle"""
    return {
        "buyer": BUYER_DEFAULT_COLUMNS,
        "capacity_manager": CAPACITY_MANAGER_DEFAULT_COLUMNS,
        "sqd": SQD_DEFAULT_COLUMNS,
    }
