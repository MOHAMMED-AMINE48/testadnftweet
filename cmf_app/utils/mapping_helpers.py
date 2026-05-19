"""
Utilitaires pour le mapping de colonnes - Réutilisable pour Acheteur et Capacity Manager
"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple, List, Optional


BUYER_MAPPING_CONFIG = {
    "required": {
        "partname": {"label": "Part Name", "key": "map_partname"},
        "apqp": {"label": "APQP", "key": "map_apqp"},
        "use_case": {"label": "Use Case", "key": "map_use_case"},
        "part_number": {"label": "Part Number", "key": "map_part_number"},
        "mix": {"label": "Mix", "key": "map_mix"},
    },
    "optional": {
        "supplier_name": {"label": "Supplier Name", "key": "map_supplier"},
        "quantity": {"label": "Quantity", "key": "map_quantity"},
        "commodity": {"label": "Commodity", "key": "map_commodity"},
        "manufacturing_cofor": {"label": "Manufacturing CO", "key": "map_mfg_co"},
        "production_location": {"label": "Production Location", "key": "map_prod_loc"},
        "buyer": {"label": "Buyer", "key": "map_buyer"},
        "purchasing_manager": {"label": "Purchasing Manager", "key": "map_purchasing_manager"},
        "gm": {"label": "GM", "key": "map_gm"},
        "sque": {"label": "SQE", "key": "map_sque"},
        "new_co": {"label": "New CO", "key": "map_new_co"},
    }
}

CAPACITY_MAPPING_CONFIG = {
    "required": {
        "part_number": {"label": "Part Number", "key": "map_cap_part_number"},
        "weekly_capacity": {"label": "Weekly Capacity", "key": "map_cap_capacity"},
        "capacity_source": {"label": "Capacity Source", "key": "map_cap_source"},
    },
    "optional": {
        "gst_no": {"label": "GST No.", "key": "map_cap_gst"},
        "comment": {"label": "Comment", "key": "map_cap_comment"},
    }
}


def show_column_mapping(
    file_columns: List[str],
    mapping_config: Dict,
    title: str = " Mapping des colonnes"
) -> Tuple[Dict, bool]:
    """
    Affiche le formulaire de mapping de colonnes avec sections Required/Optional
    
    Args:
        file_columns: Liste des colonnes du fichier source
        mapping_config: Configuration du mapping (required/optional)
        title: Titre à afficher
    
    Returns:
        Tuple: (mapping dict, is_valid: bool)
    """
    
    st.markdown(f"### {title}")
    st.caption("Associez les colonnes de votre fichier aux champs CMF")
    
    mapping = {}
    required_mapped = {}
    
    # ==================== CHAMPS OBLIGATOIRES ====================
    if mapping_config.get("required"):
        st.markdown("####  Champs Obligatoires")
        st.caption("Vous DEVEZ mapper ces champs pour l'import")
        
        req_cols = mapping_config["required"]
        num_req = len(req_cols)
        cols_req = st.columns(min(3, num_req))
        
        for idx, (field, config) in enumerate(req_cols.items()):
            with cols_req[idx % len(cols_req)]:
                selected = st.selectbox(
                    config["label"] + " *",
                    [None] + file_columns,
                    key=config["key"],
                    help="Sélectionnez la colonne correspondante"
                )
                mapping[field] = selected
                required_mapped[field] = selected is not None
    
    # ==================== CHAMPS OPTIONNELS ====================
    if mapping_config.get("optional"):
        st.markdown("####  Champs Optionnels")
        st.caption("Votre importation fonctionnera sans ces champs (remplis avec None si non mapés)")
        
        opt_cols = mapping_config["optional"]
        num_opt = len(opt_cols)
        cols_opt = st.columns(min(3, num_opt))
        
        for idx, (field, config) in enumerate(opt_cols.items()):
            with cols_opt[idx % len(cols_opt)]:
                selected = st.selectbox(
                    config["label"],
                    [None] + file_columns,
                    key=config["key"],
                    help="Optionnel - laisser vide si non souhaité"
                )
                mapping[field] = selected
    
    # ==================== VALIDATION ====================
    is_valid = all(required_mapped.values()) if required_mapped else True
    
    if not is_valid:
        missing = [config["label"] for field, config in mapping_config["required"].items() 
                   if not required_mapped.get(field)]
        st.error(f"❌ Champs obligatoires manquants: {', '.join(missing)}")
    else:
        st.success("✅ Tous les champs obligatoires sont mappés")
    
    return mapping, is_valid


def extract_row_data(row, mapping: Dict) -> Dict:
    """
    Extrait les données d'une ligne selon le mapping
    
    Args:
        row: Ligne pandas
        mapping: Dictionnaire du mapping
    
    Returns:
        Dict avec les données extraites (None si colonne non mappée/trouvée)
    """
    row_data = {}
    for cmf_field, file_col in mapping.items():
        if file_col and file_col in row.index:
            try:
                value = row[file_col]
                # Nettoyer les valeurs (strip whitespace, convert NaN to None)
                if pd.isna(value):
                    row_data[cmf_field] = None
                elif isinstance(value, str):
                    row_data[cmf_field] = value.strip() if value.strip() else None
                else:
                    row_data[cmf_field] = value
            except Exception:
                row_data[cmf_field] = None
        else:
            row_data[cmf_field] = None
    
    return row_data
