"""
Gestionnaire de mapping des colonnes pour l'importation de fichiers.
Permet aux utilisateurs de mapper les colonnes de leurs fichiers aux colonnes du CMF.
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
import pandas as pd
from utils.column_schema_manager import AVAILABLE_COLUMNS, get_all_available_columns


class ColumnMapper:
    """
    Classe pour gérer le mapping des colonnes lors de l'importation.
    Permet de créer des correspondances entre les colonnes du fichier et du CMF.
    """
    
    def __init__(self, file_columns: List[str], available_cmf_columns: Dict[str, str]):
        """
        Initialise le mapper.
        
        Args:
            file_columns: Liste des colonnes du fichier à importer
            available_cmf_columns: Dict {col_key: col_label} des colonnes disponibles du CMF
        """
        self.file_columns = file_columns
        self.available_cmf_columns = available_cmf_columns
        self.mapping = {}  # {file_col: cmf_col}
    
    def auto_map(self) -> Dict[str, str]:
        """
        Tente un mapping automatique basé sur la similarité des noms.
        
        Returns:
            Dict {file_col: cmf_col} avec les mappings trouvés
        """
        from difflib import SequenceMatcher
        
        mapping = {}
        threshold = 0.6  # Seuil de similarité (60%)
        
        for file_col in self.file_columns:
            file_normalized = file_col.lower().replace('_', ' ').replace('/', ' ')
            
            best_match = None
            best_score = threshold
            
            for cmf_col in self.available_cmf_columns.keys():
                cmf_normalized = cmf_col.lower().replace('_', ' ')
                
                similarity = SequenceMatcher(None, file_normalized, cmf_normalized).ratio()
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = cmf_col
            
            if best_match:
                mapping[file_col] = best_match
        
        self.mapping = mapping
        return mapping
    
    def set_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Définit manuellement le mapping.
        
        Args:
            mapping: Dict {file_col: cmf_col}
        """
        self.mapping = mapping
    
    def apply_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applique le mapping au DataFrame.
        
        Args:
            df: DataFrame avec colonnes du fichier
            
        Returns:
            DataFrame avec colonnes renommées selon le mapping
        """
        # Créer un mapping inverse {file_col: cmf_col} pour renommer
        reverse_mapping = {}
        for file_col, cmf_col in self.mapping.items():
            if file_col in df.columns:
                reverse_mapping[file_col] = cmf_col
        
        # Renommer les colonnes mappées
        df_mapped = df.rename(columns=reverse_mapping)
        
        # Garder seules les colonnes mappées + non mappées
        return df_mapped
    
    def get_unmapped_columns(self) -> List[str]:
        """
        Retourne les colonnes du fichier qui n'ont pas de mapping.
        
        Returns:
            Liste des colonnes non mappées
        """
        return [col for col in self.file_columns if col not in self.mapping]


def show_column_mapping_ui(
    file_columns: List[str],
    available_cmf_columns: Dict[str, str],
    role: str = "capacity_manager",
    project_name: str = "",
    reserved_columns: List[str] = None
) -> Optional[Dict[str, str]]:
    """
    Affiche l'interface UI pour mapper les colonnes et retourne le mapping automatiquement.
    
    Args:
        file_columns: Colonnes du fichier
        available_cmf_columns: Colonnes disponibles du CMF
        role: Rôle utilisateur (pour le contexte)
        project_name: Nom du projet (pour l'affichage)
        reserved_columns: Colonnes réservées pour le matching (ne pas les exposer au mapping manuel)
        
    Returns:
        mapping_dict ou None si aucun mapping
    """
    if reserved_columns is None:
        reserved_columns = []
    
    from difflib import SequenceMatcher
    
    def find_matching_reserved_column(file_col: str, reserved_list: List[str], threshold: float = 0.7) -> Optional[str]:
        """Trouve une colonne réservée correspondante avec fuzzy matching."""
        file_col_normalized = file_col.lower().replace('_', '').replace(' ', '')
        for reserved in reserved_list:
            reserved_normalized = reserved.lower().replace('_', '').replace(' ', '')
            similarity = SequenceMatcher(None, file_col_normalized, reserved_normalized).ratio()
            if similarity >= threshold:
                return reserved
        return None
    
    # Identifier les colonnes de fichier qui correspondent aux colonnes réservées
    reserved_file_columns = {}
    for file_col in file_columns:
        matched_reserved = find_matching_reserved_column(file_col, reserved_columns, threshold=0.7)
        if matched_reserved:
            reserved_file_columns[file_col] = matched_reserved
    
    st.subheader("Column Mapping")
    
    # Afficher les colonnes réservées si applicable
    if reserved_file_columns:
        st.info(f"""
        ** Matching Columns (Automatic Detection):**
        
        These columns are automatically detected and used to match records:
        - Used to find existing records in database
        
        You only need to map the remaining data columns below.
        """)
        st.divider()
    
    st.write(f"Map your file columns to {project_name} CMF fields")
    
    # Créer le mapper
    mapper = ColumnMapper(file_columns, available_cmf_columns)
    
    # Essayer un mapping automatique
    auto_mapping = mapper.auto_map()

    st.info(f"""
    **Auto-mapping found {len(auto_mapping)} matches:**
    - CMF columns are fixed below
    - For each CMF column, choose the matching column from the uploaded file
    """)

    st.divider()
    st.markdown("### Manual Mapping")

    mapping = {}
    skip_option = "-- Skip this CMF column --"
    file_options = [skip_option] + list(file_columns)

    def default_file_for_target(target_col: str) -> Optional[str]:
        for file_col, cmf_col in auto_mapping.items():
            if cmf_col == target_col:
                return file_col
        for file_col, cmf_col in reserved_file_columns.items():
            if cmf_col == target_col:
                return file_col
        if target_col in file_columns:
            return target_col
        return None

    def add_mapping_row(target_col: str, target_label: str, key_prefix: str) -> None:
        default_file_col = default_file_for_target(target_col)
        default_index = file_options.index(default_file_col) if default_file_col in file_options else 0

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(f"**{target_label}**")
        with col2:
            st.write("<-")
        with col3:
            selected_file_col = st.selectbox(
                label=f"Source for {target_label}",
                options=file_options,
                index=default_index,
                key=f"{key_prefix}_{role}_{target_col}",
                label_visibility="collapsed",
            )

        if selected_file_col != skip_option:
            mapping[selected_file_col] = target_col

    if reserved_columns:
        st.markdown("#### Matching Columns")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown("**CMF Column**")
        with col2:
            st.markdown("**<-**")
        with col3:
            st.markdown("**File Column**")

        for target_col in reserved_columns:
            add_mapping_row(target_col, target_col, "map_reserved_target")

        st.divider()

    st.markdown("#### Data Columns")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.markdown("**CMF Column**")
    with col2:
        st.markdown("**<-**")
    with col3:
        st.markdown("**File Column**")

    for target_col, target_label in available_cmf_columns.items():
        add_mapping_row(target_col, target_label, "map_data_target")

    st.divider()
    st.markdown("### Mapping Summary")

    if mapping:
        st.success(f"{len(mapping)} columns mapped:")
        for file_col, cmf_col in sorted(mapping.items(), key=lambda item: str(item[1])):
            cmf_label = available_cmf_columns.get(cmf_col, cmf_col)
            st.write(f"- `{cmf_label}` <- `{file_col}`")
    else:
        st.warning("No columns mapped")

    all_mapped_files = set(mapping.keys())
    unmapped = [col for col in file_columns if col not in all_mapped_files]
    if unmapped:
        st.warning(f"{len(unmapped)} file columns will be skipped:")
        for col in unmapped:
            st.write(f"- `{col}`")

    st.divider()
    return mapping if mapping else None
    
    st.info(f"""
    **Auto-mapping found {len(auto_mapping)} matches:**
    - These columns will be automatically mapped based on name similarity
    - You can adjust the mapping below if needed
    """)
    
    st.divider()
    
    # Afficher le formulaire de mapping
    st.markdown("### Manual Mapping (Data Columns)")
    
    # Filtrer les colonnes à mapper (exclure les colonnes réservées détectées)
    columns_to_map = [col for col in file_columns if col not in reserved_file_columns]
    
    mapping = {}
    
    # Pré-remplir le mapping avec les colonnes réservées détectées (fuzzy match)
    for file_col, reserved_col in reserved_file_columns.items():
        mapping[file_col] = reserved_col
    
    # Section 1: Rendre les colonnes réservées détectées MODIFIABLES
    if reserved_file_columns:
        st.markdown("####  Matching Columns (Modifiable)")
        st.write("You can adjust the matching columns if the auto-detection is incorrect:")
        
        for file_col in sorted(reserved_file_columns.keys()):
            col1, col2, col3 = st.columns([2, 1, 2])
            
            current_mapping = mapping.get(file_col)
            default_index = 0
            
            # Options incluent TOUS les colonnes réservées pour que l'utilisateur puisse choisir
            reserved_options = ["— Skip this column —"] + reserved_columns
            reserved_labels = ["— Skip this column —"] + reserved_columns
            
            if current_mapping and current_mapping in reserved_options:
                default_index = reserved_options.index(current_mapping)
            
            with col1:
                st.write(f"**{file_col}**")
            with col2:
                st.write("→")
            with col3:
                selected_cmf = st.selectbox(
                    label=f"Map {file_col}",
                    options=reserved_options,
                    format_func=lambda x: reserved_labels[reserved_options.index(x)],
                    index=default_index,
                    key=f"map_reserved_{file_col}_{role}",
                    label_visibility="collapsed"
                )
                
                # Mettre à jour le mapping
                if selected_cmf != "— Skip this column —":
                    mapping[file_col] = selected_cmf
                else:
                    # Si l'utilisateur skip, retirer du mapping
                    if file_col in mapping:
                        del mapping[file_col]
        
        st.divider()
    
    # Section 2: Mapper les autres colonnes avec APQP et Part Number disponibles
    st.markdown("####  Data Columns")
    
    # Créer des colonnes pour le mapping
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown("**File Column**")
    with col2:
        st.markdown("**→**")
    with col3:
        st.markdown("**CMF Column**")
    
    st.divider()
    
    # Pour chaque colonne du fichier NON-réservée, offrir un selectbox
    for file_col in sorted(columns_to_map):
        col1, col2, col3 = st.columns([2, 1, 2])
        
        # Obtenir le mapping par défaut (auto-mapping si disponible)
        default_cmf_col = auto_mapping.get(file_col, None)
        default_index = None
        
        # INCLURE les colonnes réservées dans les choix (APQP, Part Number disponibles)
        cmf_col_options = ["— Skip this column —"] + list(available_cmf_columns.keys())
        cmf_col_labels = ["— Skip this column —"] + [
            f"{available_cmf_columns[k]}" for k in available_cmf_columns.keys()
        ]
        
        if default_cmf_col and default_cmf_col in available_cmf_columns:
            default_index = cmf_col_options.index(default_cmf_col)
        else:
            default_index = 0
        
        with col1:
            st.write(f"**{file_col}**")
        
        with col2:
            st.write("→")
        
        with col3:
            selected_cmf = st.selectbox(
                label=f"Map {file_col}",
                options=cmf_col_options,
                format_func=lambda x: cmf_col_labels[cmf_col_options.index(x)],
                index=default_index,
                key=f"map_data_{file_col}_{role}",
                label_visibility="collapsed"
            )
            
            # Ajouter au mapping si sélectionné (pas "Skip")
            if selected_cmf != "— Skip this column —":
                mapping[file_col] = selected_cmf
    
    st.divider()
    
    # Afficher un résumé du mapping
    st.markdown("### Mapping Summary")
    
    # Afficher les colonnes réservées - MODIFIÉES par l'utilisateur
    actual_reserved_mapping = {k: v for k, v in mapping.items() if k in reserved_file_columns}
    if actual_reserved_mapping:
        st.info("** Matching Columns (Modifiable):**")
        for file_col, cmf_col in sorted(actual_reserved_mapping.items()):
            st.write(f"  • `{file_col}` → `{cmf_col}`")
    
    # Afficher les colonnes de données mappées (inclut maintenant APQP et Part Number si mappés)
    data_mapping = {k: v for k, v in mapping.items() if k not in reserved_file_columns}
    if data_mapping:
        st.success(f" **{len(data_mapping)} data columns mapped:**")
        for file_col, cmf_col in sorted(data_mapping.items()):
            cmf_label = available_cmf_columns.get(cmf_col, cmf_col)
            st.write(f"  • `{file_col}` → `{cmf_label}`")
    else:
        st.warning(" No data columns mapped")
    
    # Afficher les colonnes non-mappées
    all_mapped_files = set(mapping.keys())
    unmapped = [col for col in file_columns if col not in all_mapped_files]
    if unmapped:
        st.warning(f" **{len(unmapped)} columns will be skipped:**")
        for col in unmapped:
            st.write(f"  • `{col}`")
    
    st.divider()
    
    # Retourner le mapping complet
    if mapping:
        return mapping
    else:
        return None


def show_unique_column_mapping_ui(
    file_columns: List[str],
    mapping_targets: List[str],
    mandatory_keys: List[str] = None,
    role: str = "capacity_manager",
    project_name: str = "",
) -> Optional[Dict[str, Optional[str]]]:
    """
    Affiche un mapping unique CMF -> colonne fichier.

    Chaque cible CMF peut être associée à une colonne source du fichier,
    et une même colonne source peut être choisie pour plusieurs cibles.
    """
    mandatory_keys = mandatory_keys or []

    st.subheader("Column Mapping")
    st.markdown("### Mapping des colonnes fichier → colonnes CMF")
    st.write(f"Map your file columns to {project_name} CMF fields")
    st.caption("Les colonnes obligatoires sont APQP GRID et PART NUMBER. Les autres colonnes sont optionnelles.")

    file_options = [None] + list(file_columns)

    def _format_option(value: Optional[str]) -> str:
        return "— Non mappé —" if value is None else str(value)

    mapping: Dict[str, Optional[str]] = {}

    for target in mapping_targets:
        default_value = target if target in file_columns else None
        default_index = file_options.index(default_value) if default_value in file_options else 0
        is_required = target in mandatory_keys

        selected_file_col = st.selectbox(
            label=f"{target}",
            options=file_options,
            index=default_index,
            key=f"unique_map_{role}_{project_name}_{target}",
            format_func=_format_option,
            help="Obligatoire" if is_required else "Optionnel",
        )
        mapping[target] = selected_file_col

    errors = []
    for key in mandatory_keys:
        if not mapping.get(key):
            errors.append(f"Mapper obligatoirement la colonne « {key} »")

    if errors:
        st.error("\n".join(errors))
        st.stop()

    return mapping


def preview_unique_mapped_data(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]],
    max_rows: int = 5,
) -> None:
    """Affiche un aperçu en gardant les cibles CMF comme colonnes de sortie."""
    st.markdown("### Preview After Mapping")

    preview_data = {}
    for target_col, source_col in mapping.items():
        if source_col and source_col in df.columns:
            preview_data[target_col] = df[source_col]
        else:
            preview_data[target_col] = [None] * len(df)

    df_preview = pd.DataFrame(preview_data)
    st.dataframe(
        df_preview.head(max_rows),
        use_container_width=True,
        height=300,
    )
    st.caption(f"Showing {min(max_rows, len(df_preview))} of {len(df_preview)} rows")




def preview_mapped_data(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    max_rows: int = 5
) -> None:
    """
    Affiche un aperçu des données après mapping.
    
    Args:
        df: DataFrame source
        mapping: Mapping appliqué
        max_rows: Nombre de lignes à afficher
    """
    st.markdown("### Preview After Mapping")
    
    # Appliquer le mapping
    df_mapped = df.rename(columns=mapping)
    
    # Garder seules les colonnes mappées
    mapped_cols = list(mapping.values())
    df_preview = df_mapped[mapped_cols] if mapped_cols else df_mapped
    
    st.dataframe(
        df_preview.head(max_rows),
        use_container_width=True,
        height=300
    )
    
    st.caption(f"Showing {min(max_rows, len(df_preview))} of {len(df_preview)} rows")


def get_column_mapping_key(project_id: int, role: str) -> str:
    """
    Génère une clé unique pour stocker le mapping dans la session.
    
    Args:
        project_id: ID du projet
        role: Rôle utilisateur
        
    Returns:
        Clé de stockage
    """
    return f"column_mapping_{project_id}_{role}"


def save_column_mapping(project_id: int, role: str, mapping: Dict[str, str]) -> None:
    """
    Sauvegarde le mapping dans la session Streamlit.
    
    Args:
        project_id: ID du projet
        role: Rôle utilisateur
        mapping: Dict {file_col: cmf_col}
    """
    key = get_column_mapping_key(project_id, role)
    st.session_state[key] = mapping


def load_column_mapping(project_id: int, role: str) -> Optional[Dict[str, str]]:
    """
    Charge le mapping depuis la session Streamlit.
    
    Args:
        project_id: ID du projet
        role: Rôle utilisateur
        
    Returns:
        Mapping ou None si non disponible
    """
    key = get_column_mapping_key(project_id, role)
    return st.session_state.get(key, None)


class CompositeKeyMatcher:
    """
    Matcher pour appariement composite key (APQP + Partnumber).
    Utilisé pour SQD et Capacity Manager pour matcher les fichiers d'import
    avec les enregistrements existants en utilisant APQP + Partnumber.
    """
    
    def __init__(self, existing_records: List[dict], composite_keys: List[str] = None):
        """
        Initialise le matcher.
        
        Args:
            existing_records: Liste des enregistrements existants (dicts)
            composite_keys: Clés pour le composite (par défaut ['apqp', 'part_number'])
        """
        self.composite_keys = composite_keys or ['apqp', 'part_number']
        self.existing_records = existing_records
        self.composite_map = self._build_composite_map()
    
    def _build_composite_map(self) -> Dict[str, dict]:
        """
        Construit une map de composite keys vers enregistrements.
        
        Returns:
            Dict {composite_key_str: record}
        """
        composite_map = {}
        for record in self.existing_records:
            # Construire la clé composite
            key_parts = []
            for key_field in self.composite_keys:
                value = record.get(key_field, '')
                if isinstance(value, (int, float)):
                    key_parts.append(str(value).strip())
                else:
                    key_parts.append(str(value).strip() if value else '')
            
            # Créer une clé unique: "apqp|partnumber"
            composite_key = '|'.join(key_parts)
            if composite_key and all(p for p in key_parts):  # Tous les éléments non vides
                composite_map[composite_key] = record
        
        return composite_map
    
    def find_matching_record(self, file_row: pd.Series) -> Optional[dict]:
        """
        Trouve l'enregistrement correspondant pour une ligne de fichier.
        
        Args:
            file_row: Ligne du fichier (pandas Series)
            
        Returns:
            Enregistrement correspondant ou None
        """
        # Construire la clé composite du fichier
        key_parts = []
        for key_field in self.composite_keys:
            value = file_row.get(key_field, '')
            if pd.isna(value):
                return None
            if isinstance(value, (int, float)):
                key_parts.append(str(value).strip())
            else:
                key_parts.append(str(value).strip() if value else '')
        
        # Créer la clé composite
        composite_key = '|'.join(key_parts)
        
        # Chercher dans la map
        if composite_key in self.composite_map:
            return self.composite_map[composite_key]
        
        return None
    
    def get_composite_key_from_record(self, record: dict) -> str:
        """
        Extrait la clé composite d'un enregistrement.
        
        Args:
            record: Enregistrement (dict)
            
        Returns:
            Clé composite sous forme de string
        """
        key_parts = []
        for key_field in self.composite_keys:
            value = record.get(key_field, '')
            if isinstance(value, (int, float)):
                key_parts.append(str(value).strip())
            else:
                key_parts.append(str(value).strip() if value else '')
        
        return '|'.join(key_parts)


def validate_mapping_for_composite_matching(
    mapping: Dict[str, str],
    required_keys: List[str] = ['apqp', 'part_number']
) -> Tuple[bool, List[str]]:
    """
    Valide que le mapping contient les colonnes nécessaires pour le matching composite.
    
    Args:
        mapping: Mapping {file_col: cmf_col}
        required_keys: Colonnes CMF requises pour le matching
        
    Returns:
        (is_valid, missing_keys)
    """
    mapped_cmf_cols = set(mapping.values())
    missing_keys = [key for key in required_keys if key not in mapped_cmf_cols]
    
    return len(missing_keys) == 0, missing_keys


def apply_mapping_and_match(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    existing_records: List[dict],
    composite_keys: List[str] = ['apqp', 'part_number'],
    data_role_columns: List[str] = None
) -> Tuple[pd.DataFrame, Dict[str, int], Dict[str, str]]:
    """
    Applique le mapping aux colonnes du fichier et fait correspondre avec les enregistrements existants.
    
    Args:
        df: DataFrame du fichier
        mapping: Mapping {file_col: cmf_col}
        existing_records: Enregistrements existants de la BD
        composite_keys: Clés pour le matching composite
        data_role_columns: Colonnes de données spécifiques au rôle (CM, SQD, etc.)
        
    Returns:
        (df_mapped, match_results, errors)
        - df_mapped: DataFrame avec colonnes mappées et colonne 'record_id' ajoutée
        - match_results: {file_line: matched_record_id} pour les lines matchées
        - errors: {file_line: error_message} pour les non-matchées
    """
    # Appliquer le mapping
    df_mapped = df.rename(columns=mapping)
    
    # Créer le matcher
    matcher = CompositeKeyMatcher(existing_records, composite_keys)
    
    match_results = {}
    errors = {}
    record_ids = []
    
    # Pour chaque ligne, chercher le matching record
    for idx, row in df_mapped.iterrows():
        matching_record = matcher.find_matching_record(row)
        
        if matching_record:
            record_id = matching_record.get('id')
            match_results[idx] = record_id
            record_ids.append(record_id)
        else:
            # Créer un message d'erreur avec les valeurs
            apqp_val = row.get('apqp', 'N/A')
            pn_val = row.get('part_number', 'N/A')
            errors[idx] = f"No match found for APQP={apqp_val}, Part#={pn_val}"
            record_ids.append(None)
    
    # Ajouter la colonne des record IDs
    df_mapped['_record_id'] = record_ids
    
    return df_mapped, match_results, errors
