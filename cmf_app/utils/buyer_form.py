"""
Logique de formulaire Acheteur - Peut être utilisée dans buyer.py (page autonome) ou app.py (routeur)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from models.cmf_schema import CMFRecord
from config.settings import RecordStatus, UserRole, ROLE_PERMISSIONS
from services.validation_rules import ValidationRules
from utils.mapping_helpers import BUYER_MAPPING_CONFIG, show_column_mapping, extract_row_data


def validate_buyer_record(data: dict):
    """
    Valide un record selon les règles métier Acheteur
    
    Champs obligatoires:
    - partname
    - apqp
    - use_case
    - part_number (≠ NEW)
    - mix
    
    Champs optionnels:
    - supplier_name
    - quantity
    """
    errors = []
    warnings = []
    
    # Champs obligatoires (selon spécification mise à jour)
    required_fields = {
        "partname": "Part Name",
        "apqp": "APQP",
        "use_case": "Use Case",
        "part_number": "Part Number",
        "mix": "Mix"
    }
    
    for field, label in required_fields.items():
        value = data.get(field)
        
        # Vérifier le vide
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f" {label} est obligatoire")
            continue
        
        # Part Number spécial: ne pas accepter "NEW"
        if field == "part_number" and value == "NEW":
            errors.append(f" {label} ne peut pas être 'NEW'")
        
        # Mix validation
        if field == "mix":
            try:
                mix_val = float(value)
                if mix_val < 0 or mix_val > 1:
                    errors.append(f" {label} doit être entre 0 et 1")
            except (ValueError, TypeError):
                errors.append(f" {label} doit être un nombre")
    
    # Validations spécifiques pour champs optionnels
    if data.get("quantity"):
        try:
            quantity = float(data.get("quantity", 0))
            if quantity <= 0:
                errors.append(" Quantity doit être > 0")
        except (ValueError, TypeError):
            errors.append(" Quantity doit être un nombre")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }



def create_cmf_record_from_form_data(form_data: dict, user: str, role: str, status: str = None):
    """Crée un CMFRecord à partir des données du formulaire"""
    
    # Déterminer le statut automatiquement si pas fourni
    if not status:
        status = RecordStatus.PRESOURCING.value if (
            not form_data.get("part_number") or 
            form_data.get("part_number") == "NEW"
        ) else RecordStatus.ACTIVE.value
    
    return CMFRecord(
        row_id=None,
        partname=form_data.get("partname"),
        part_number=form_data.get("part_number"),
        commodity=form_data.get("commodity"),
        quantity=float(form_data.get("quantity", 0)) if form_data.get("quantity") else 0,
        supplier_name=form_data.get("supplier_name"),
        manufacturing_cofor=form_data.get("manufacturing_cofor"),
        production_location=form_data.get("production_location"),
        use_case=form_data.get("use_case"),
        apqp=form_data.get("apqp"),
        new_co=form_data.get("new_co"),
        buyer=form_data.get("buyer"),
        purchasing_manager=form_data.get("purchasing_manager"),
        gm=form_data.get("gm"),
        sque=form_data.get("sque"),
        mix=form_data.get("mix"),
        status=status,
        last_updated=datetime.now().isoformat(),
        updated_by=user,
        # Autres champs Capacity Manager et SQD restent vides
        scr=None, link_to_doc_info=None, gst_no=None,
        capacity_source=None, calculated_weekly_capacity=0,
        cm_comment=None,
        weekly_capacity_to_measure=None, k9_sck=None,
        cat1_forecasted_date=None, cat1_type=None,
        cat2_forecasted_date=None, cat2_type=None,
        cat3_forecasted_date=None, cat3_type=None,
        weekly_capacity_measured=None, estimated_target=None,
        cat1_evaluation=None, cat2_evaluation=None, cat3_evaluation=None,
        shared_folder=None, sqd_comment=None, sque_team=None,
    )


def show_manual_entry_form(services: dict, current_user: str):
    """Affiche le formulaire de saisie manuelle"""
    
    excel_service = services.get("excel_service")
    audit_service = services.get("audit_service")
    
    if not excel_service or not audit_service:
        st.error(" Services non disponibles.")
        return
    
    with st.form("buyer_form"):
        st.write("**Champs Obligatoires** ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            partname = st.text_input(
                "Part Name *",
                placeholder="ex: Compresseur AC-100",
                help="Nom du composant"
            )
            
            # APQP - OBLIGATOIRE
            apqp = st.text_input(
                "APQP *",
                placeholder="ex: rev_1",
                help="APQP obligatoire"
            )
            
            part_number = st.text_input(
                "Part Number *",
                placeholder="ex: AC100-V2",
                help="Code interne ou externe du composant (ne peut pas être 'NEW')"
            )
            
            mix = st.slider(
                "Mix *",
                min_value=0.0,
                max_value=1.0,
                value=1.0,
                step=0.01,
                help="Ratio de mélange (0 à 1)"
            )
        
        with col2:
            # Use Case - OBLIGATOIRE
            use_case = st.text_input(
                "Use Case *",
                placeholder="ex: Automotive",
                help="Cas d'usage obligatoire"
            )
            
            commodity = st.text_input(
                "Commodity",
                placeholder="ex: Moteur",
                help="Catégorie du composant"
            )
            
            manufacturing_cofor = st.text_input(
                "Manufacturing CO",
                placeholder="ex: Vietnam",
                help="Pays de fabrication"
            )
            
            quantity = st.number_input(
                "Quantity",
                value=0,
                min_value=0,
                step=1,
                help="Quantité à produire/acheter (optionnel)"
            )
        
        # Champs optionnels supplémentaires
        with st.expander("Champs Optionnels"):
            col3, col4 = st.columns(2)
            
            with col3:
                supplier_name = st.text_input("Supplier Name", placeholder="ex: MOTOR_TECH_SA")
                production_location = st.text_input("Production Location", placeholder="ex: Plant_1")
                purchasing_manager = st.text_input("Purchasing Manager", placeholder="ex: John Doe")
            
            with col4:
                buyer = st.text_input("Buyer", placeholder="ex: Jane Doe")
                gm = st.text_input("GM", placeholder="ex: Manager Name")
                new_co = st.text_input("New CO", placeholder="ex: Y/N")
                sque = st.text_input("SQE", placeholder="ex: SQE_001")
        
        # Boutons
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn1:
            submitted = st.form_submit_button(
                " Enregistrer",
                use_container_width=True,
                type="primary"
            )
        
        with col_btn2:
            reset = st.form_submit_button(" Réinitialiser", use_container_width=True)
        
        with col_btn3:
            preview = st.form_submit_button(" Aperçu", use_container_width=True)
    
    # Traiter la soumission
    if submitted:
        form_data = {
            "partname": partname,
            "part_number": part_number or None,
            "commodity": commodity or None,
            "quantity": quantity if quantity > 0 else None,
            "supplier_name": supplier_name or None,
            "manufacturing_cofor": manufacturing_cofor or None,
            "production_location": production_location or None,
            "use_case": use_case or None,
            "apqp": apqp or None,
            "new_co": new_co or None,
            "buyer": buyer or None,
            "purchasing_manager": purchasing_manager or None,
            "gm": gm or None,
            "sque": sque or None,
            "mix": mix,
        }
        
        validation = validate_buyer_record(form_data)
        
        if not validation["is_valid"]:
            st.error(" Erreurs de validation:")
            for error in validation["errors"]:
                st.error(error)
            st.stop()
        
        if validation["warnings"]:
            st.warning(" Avertissements:")
            for warning in validation["warnings"]:
                st.warning(warning)
        
        # Créer et enregistrer
        try:
            new_record = create_cmf_record_from_form_data(
                form_data,
                user=current_user,
                role="BUYER"
            )
            
            excel_service.append_rows_to_cmf(
                [new_record],
                user=current_user,
                role="BUYER"
            )
            
            audit_service.log_action(
                action="MANUAL_ENTRY",
                user=current_user,
                role="BUYER",
                table="CMF",
                details=f"Record créé: {form_data['partname']}, Status: {new_record.status}",
            )
            
            st.success(f"""
             Record créé avec succès!
            - Part Name: {form_data['partname']}
            - Supplier: {form_data['supplier_name']}
            - Status: {new_record.status}
            """)

        
        except Exception as e:
            st.error(f" Erreur: {str(e)}")


def show_file_import_form(services: dict, current_user: str):
    """Affiche le formulaire d'import fichier avec mappage flexible des colonnes"""
    
    excel_service = services.get("excel_service")
    audit_service = services.get("audit_service")
    
    if not excel_service or not audit_service:
        st.error(" Services non disponibles.")
        return
    
    uploaded_file = st.file_uploader(
        " Sélectionnez un fichier (Excel/CSV)",
        type=["xlsx", "csv", "xls"],
        help="Max 25 MB"
    )
    
    if uploaded_file:
        try:
            # Lire le fichier
            if uploaded_file.name.endswith(".csv"):
                df_uploaded = pd.read_csv(uploaded_file)
            else:
                df_uploaded = pd.read_excel(uploaded_file)
            
            st.info(f" Fichier chargé: {uploaded_file.name} ({len(df_uploaded)} lignes)")
            
            with st.expander(" Aperçu", expanded=True):
                st.dataframe(df_uploaded, use_container_width=True)
            
            # Interface de mappage unifiée (Required + Optional)
            st.markdown("### 🔗 Mapping des colonnes")
            file_columns = df_uploaded.columns.tolist()
            
            mapping, is_mapping_valid = show_column_mapping(file_columns, BUYER_MAPPING_CONFIG)
            
            if not is_mapping_valid:
                st.stop()
            
            # Confirmer l'import
            if st.button(" Confirmer l'import", type="primary", use_container_width=True):
                try:
                    processed_records = []
                    errors = []
                    
                    for idx, row in df_uploaded.iterrows():
                        try:
                            # Extraire les données avec gestion des NaN et whitespace
                            row_data = extract_row_data(row, mapping)
                            
                            # Valider les champs obligatoires
                            validation = validate_buyer_record(row_data)
                            if not validation["is_valid"]:
                                errors.append(f"Ligne {idx + 2}: {', '.join(validation['errors'])}")
                                continue
                            
                            # Créer le record
                            new_record = create_cmf_record_from_form_data(
                                row_data,
                                user=current_user,
                                role="BUYER"
                            )
                            
                            processed_records.append(new_record)
                        
                        except Exception as e:
                            errors.append(f"Ligne {idx + 2}: {str(e)}")
                    
                    # Afficher les résultats
                    if errors:
                        st.warning(f" {len(errors)} erreur(s) lors du traitement:")
                        for error in errors[:5]:
                            st.warning(f"  • {error}")
                        if len(errors) > 5:
                            st.warning(f"  ... et {len(errors) - 5} autre(s)")
                    
                    if processed_records:
                        excel_service.append_rows_to_cmf(
                            processed_records,
                            user=current_user,
                            role="BUYER"
                        )
                        
                        audit_service.log_action(
                            action="IMPORT",
                            user=current_user,
                            role="BUYER",
                            table="CMF",
                            details=f"Import: {uploaded_file.name} ({len(processed_records)} records importés)",
                        )
                        
                        st.success(f"""
                         Import réussi!
                        - {len(processed_records)} records importés
                        - {len(errors)} erreurs
                        """)
                    else:
                        st.error(" Aucun record valide n'a pu être importé")
                
                except Exception as e:
                    st.error(f" Erreur lors de l'import: {str(e)}")
        
        except Exception as e:
            st.error(f" Erreur lors du chargement du fichier: {str(e)}")
