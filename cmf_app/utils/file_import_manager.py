"""
Gestionnaire d'import pour fichiers CSV et Excel.
Supporte l'upload de fichiers et parsing des données.
"""

import pandas as pd
import streamlit as st
from typing import Optional, Tuple, Dict, List, Any
import io
from .encoding_handler import safe_decode_value


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie un DataFrame en décodant les valeurs avec problèmes d'encodage.
    
    Args:
        df: DataFrame à nettoyer
        
    Returns:
        DataFrame nettoyé
    """
    if df.empty:
        return df
    
    # Nettoyer chaque valeur
    for col in df.columns:
        if df[col].dtype == 'object':  # Colonnes de texte
            df[col] = df[col].apply(lambda x: safe_decode_value(x))
    
    return df


def read_uploaded_file(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Lit un fichier uploadé (CSV ou Excel) avec gestion robuste d'encodage.
    
    Args:
        uploaded_file: Fichier uploadé par Streamlit
        
    Returns:
        DataFrame ou None si erreur
    """
    try:
        if uploaded_file is None:
            return None
            
        file_name = uploaded_file.name.lower()
        df = None
        
        if file_name.endswith('.csv'):
            # Essayer différents encodages pour CSV
            encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    # Réinitialiser la position du fichier
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break  # Succès !
                except (UnicodeDecodeError, UnicodeWarning):
                    continue  # Essayer le prochain encodage
            
            # Si tous les encodages échouent, utiliser le mode 'replace'
            if df is None:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8', errors='replace')
        
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        
        else:
            st.error(" Format non supporté. Utilisez CSV ou Excel (.xlsx, .xls)")
            return None
        
        if df is None:
            st.error(" Impossible de lire le fichier")
            return None
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Nettoyer les valeurs d'encodage problématiques
        df = _clean_dataframe(df)
        
        return df
    
    except Exception as e:
        st.error(f" Erreur lors de la lecture du fichier: {str(e)}")
        return None


def normalize_column_name(name: str) -> str:
    """
    Normalise le nom d'une colonne du fichier et le mappe aux colonnes du système.
    
    Args:
        name: Nom de colonne depuis le fichier
        
    Returns:
        Nom de colonne mappé au système
    """
    name = name.strip().lower().replace(' ', '_').replace('/', '_')
    
    # Mappings courants
    mapping = {
        'cmf_line_no': 'cmf_line_no',
        'cmfline': 'cmf_line_no',
        'sourcing_rfq_odm_fete': 'sourcing_rfq_odm_fete',
        'apqp_grid': 'apqp_grid',
        'apqpgrid': 'apqp_grid',
        'n_fac_rfq_pd_letter': 'fac_rfq_pd_letter',
        'fac_rfq_pd_letter': 'fac_rfq_pd_letter',
        'use_cases': 'use_cases',
        'part_number': 'part_number',
        'partnumber': 'part_number',
        'part#': 'part_number',
        'pn': 'part_number',
        'process_part_coefficient': 'process_part_coefficient',
        'supplier_name': 'supplier_name',
        'suppliername': 'supplier_name',
        'country': 'country',
        'location': 'location',
        'cofor': 'cofor',
        'sqe': 'sqe',
        'program_buyer': 'program_buyer',
        'buyer': 'program_buyer',
        'weekly_capacity_contracted': 'weekly_capacity_contracted',
        'capacity_step_contracted': 'capacity_step_contracted',
        'lead_time_capacity_step_weeks': 'lead_time_capacity_step_weeks',
        'investment_impact_capacity_step_euro': 'investment_impact_capacity_step_euro',
        'year_of_max_need': 'year_of_max_need',
        'gor_supplier_capacity_contracted': 'gor_supplier_capacity_contracted',
        'scr_shared_folder': 'scr_shared_folder',
        'scr_date': 'scr_date',
        'mix_pct': 'mix_pct',
        'last_weekly_capacity_requested': 'last_weekly_capacity_requested',
        'capacity_step_parts_per_week': 'capacity_step_parts_per_week',
        'peak_year': 'peak_year',
        'weekly_capacity_to_measure': 'weekly_capacity_to_measure',
        'cat1_forecasted_date': 'cat1_forecasted_date',
        'cat2_forecasted_date': 'cat2_forecasted_date',
        'last_cat_date_done': 'last_cat_date_done',
        'cat_type': 'cat_type',
        'weekly_capacity_measured': 'weekly_capacity_measured',
        'weekly_capacity_estimated': 'weekly_capacity_estimated',
        'cat_valuation': 'cat_valuation',
        'shared_folder_link': 'shared_folder_link',
        'comments': 'comments',
        'quantity': 'quantity',
        'qty': 'quantity',
        'supplier': 'supplier_name',
        'apqp': 'apqp_grid',
        'commodity': 'commodity',
        'mix': 'mix_pct',
        'mix_ratio': 'mix_pct',
        'mixratio': 'mix_pct',
    }
    
    return mapping.get(name, name)


def preview_file(df: pd.DataFrame, max_rows: int = 5) -> None:
    """
    Affiche un aperçu du fichier.
    
    Args:
        df: DataFrame à prévisualiser
        max_rows: Nombre de lignes à afficher
    """
    st.subheader(" Aperçu du fichier")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lignes", len(df))
    with col2:
        st.metric("Colonnes", len(df.columns))
    with col3:
        st.metric("Colonnes manquantes", len(df.columns[df.isna().any()]))
    
    st.dataframe(df.head(max_rows), use_container_width=True)


def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Valide que toutes les colonnes requises sont présentes.
    
    Args:
        df: DataFrame à valider
        required_columns: Liste des colonnes requises
        
    Returns:
        (est_valide, colonnes_manquantes)
    """
    df_columns = set(df.columns)
    missing = [col for col in required_columns if col not in df_columns]
    
    return len(missing) == 0, missing


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Renomme les colonnes du DataFrame selon le mapping.
    
    Args:
        df: DataFrame source
        mapping: Dict {column_in_file: column_in_system}
        
    Returns:
        DataFrame avec colonnes renommées
    """
    available_cols = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=available_cols)


def show_import_dialog(
    title: str = " Importer des données",
    file_label: str = "Sélectionnez un fichier CSV ou Excel",
    required_columns: Optional[List[str]] = None
) -> Optional[pd.DataFrame]:
    """
    Affiche le dialogue d'import et retourne le DataFrame.
    
    Args:
        title: Titre du dialogue
        file_label: Label du widget de fichier
        required_columns: Colonnes requises (optionnel)
        
    Returns:
        DataFrame importé ou None
    """
    with st.container():
        st.subheader(title)
        
        uploaded_file = st.file_uploader(
            file_label,
            type=["csv", "xlsx", "xls"],
            key=f"import_{title.replace(' ', '_')}"
        )
        
        if uploaded_file is None:
            st.info(" Aucun fichier sélectionné")
            return None
        
        df = read_uploaded_file(uploaded_file)
        
        if df is None:
            return None
        
        # Afficher aperçu
        preview_file(df)
        
        # Valider colonnes requises
        if required_columns:
            is_valid, missing = validate_required_columns(df, required_columns)
            
            if not is_valid:
                st.warning(f" Colonnes manquantes: {', '.join(missing)}")
                return None
            else:
                st.success(f" Toutes les colonnes requises sont présentes")
        
        return df


def export_dataframe_to_excel(df: pd.DataFrame, file_name: str = "export.xlsx") -> bytes:
    """
    Exporte un DataFrame au format Excel.
    
    Args:
        df: DataFrame à exporter
        file_name: Nom du fichier (sans extension)
        
    Returns:
        Bytes du fichier Excel
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
    
    return output.getvalue()


def export_dataframe_to_csv(df: pd.DataFrame, file_name: str = "export.csv") -> str:
    """
    Exporte un DataFrame au format CSV.
    
    Args:
        df: DataFrame à exporter
        file_name: Nom du fichier (sans extension)
        
    Returns:
        Contenu CSV en string
    """
    return df.to_csv(index=False)
