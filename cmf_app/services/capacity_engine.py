"""
Moteur de calcul de capacité.
Gère le join CMF ↔ sources capacité et la mise à jour conditionnelle.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd

from models.cmf_schema import CMFRecord, CapacitySource, ValidationResult
from services.validation_rules import ValidationRules


# ==================== UTILITY FUNCTIONS ====================
def find_cmf_record_by_apqp_and_partnumber(
    records: List[CMFRecord],
    apqp: str,
    part_number: str,
) -> Optional[CMFRecord]:
    """
    Cherche un record dans le CMF par APQP et Part Number.
    
    Cette fonction valide que les données saisies par Capacity Manager ou SQD
    correspondent à un record existant créé par le Buyer.
    
    Args:
        records: Liste de CMFRecord (lecture du CMF via read_cmf_records())
        apqp: Code APQP de la donnée saisie/importée
        part_number: Part Number de la donnée saisie/importée
    
    Returns:
        CMFRecord trouvé (premier match), ou None si aucun match
    
    Raises:
        Aucune exception - retourne None en cas de non-match
    
    Examples:
        >>> records = excel_service.read_cmf_records()
        >>> record = find_cmf_record_by_apqp_and_partnumber(
        ...     records=records, 
        ...     apqp="APQ123", 
        ...     part_number="PN-001"
        ... )
        >>> if record is None:
        ...     st.error("APQP/PartNumber not found in this CMF")
    """
    if not records:
        return None
    
    # Nettoyer les inputs
    apqp_clean = str(apqp).strip() if apqp else ""
    part_number_clean = str(part_number).strip() if part_number else ""
    
    # Chercher un match exact
    for record in records:
        record_apqp = str(record.apqp).strip() if record.apqp else ""
        record_part_number = str(record.part_number).strip() if record.part_number else ""
        
        if (record_apqp == apqp_clean and 
            record_part_number == part_number_clean):
            return record
    
    return None


class CapacityEngine:
    """
    Moteur centralisé pour les calculs de capacité.
    
    Responsabilités:
    - Join CMF ↔ sources de capacité
    - Calcul de la capacité en fonction du Mix
    - Gestion du presourcing (pas de capacité trouvée)
    - Mise à jour conditionnelle des records
    """
    
    def __init__(self):
        """Initialise le moteur"""
        self.capacity_sources: Dict[str, List[CapacitySource]] = {
            "LTOS": [],
            "GST": [],
            "FETE": [],
            "TKO": [],
        }
    
    def register_capacity_sources(
        self,
        source_name: str,
        sources: List[CapacitySource]
    ) -> None:
        """Enregistre une liste de sources de capacité"""
        if source_name not in self.capacity_sources:
            raise ValueError(f"Source inconnue: {source_name}")
        
        # Valider chaque source
        valid_sources = []
        for source in sources:
            validation = ValidationRules.validate_capacity_source(source)
            if validation.is_valid:
                valid_sources.append(source)
        
        self.capacity_sources[source_name] = valid_sources
    
    def find_matching_capacity(
        self,
        part_number: str,
        supplier_name: str,
        capacity_source: Optional[str] = None,
    ) -> Optional[CapacitySource]:
        """
        Cherche une capacité correspondante pour un Part Number et fournisseur.
        
        Args:
            part_number: Numéro de pièce
            supplier_name: Nom du fournisseur
            capacity_source: Source préférée (optionnel)
        
        Returns:
            CapacitySource trouvée ou None
        """
        # Si une source est spécifiée, chercher d'abord là
        if capacity_source and capacity_source in self.capacity_sources:
            for source in self.capacity_sources[capacity_source]:
                if (source.part_number == part_number and
                    source.supplier_name == supplier_name):
                    return source
        
        # Sinon, chercher dans toutes les sources
        for source_list in self.capacity_sources.values():
            for source in source_list:
                if (source.part_number == part_number and
                    source.supplier_name == supplier_name):
                    return source
        
        return None
    
    def calculate_capacity(
        self,
        base_capacity: float,
        mix_ratio: float = 1.0,
    ) -> float:
        """
        Calcule la capacité avec application du mix ratio.
        
        Formule: calculated_capacity = base_capacity * mix_ratio
        
        Args:
            base_capacity: Capacité de base (parts/week)
            mix_ratio: Ratio de mix (0 à 1)
        
        Returns:
            Capacité calculée
        """
        if base_capacity <= 0:
            return 0.0
        
        calculated = base_capacity * mix_ratio
        return max(0.0, calculated)  # Pas de négatif
    
    def update_capacity_for_record(
        self,
        record: CMFRecord,
        force_update: bool = False,
    ) -> Tuple[bool, str]:
        """
        Met à jour la capacité calculée d'un record de manière conditionnelle.
        
        Règles:
        - Si Part Number vide ou "NEW" → statut PRESOURCING
        - Cherche dans les sources de capacité
        - Si trouvée → calcul et mise à jour
        - Si pas trouvée → statut PRESOURCING
        - N'overwrite que si la capacité a changé (mise à jour conditionnelle)
        
        Args:
            record: Record à mettre à jour
            force_update: Force la mise à jour même si aucune capacité trouvée
        
        Returns:
            Tuple: (success, message)
        """
        # Vérifier presourcing
        if (not record.part_number or 
            record.part_number.strip() == "" or 
            record.part_number == "NEW"):
            record.status = "PRESOURCING"
            return True, "Record en presourcing (Part Number vide/NEW)"
        
        # Chercher dans les sources
        capacity_source = self.find_matching_capacity(
            part_number=record.part_number,
            supplier_name=record.supplier_name,
            capacity_source=record.capacity_source if record.capacity_source else None,
        )
        
        if not capacity_source:
            if force_update:
                record.status = "PRESOURCING"
                record.calculated_weekly_capacity = 0.0
                return True, "Aucune capacité trouvée → PRESOURCING"
            return False, "Aucune source de capacité trouvée"
        
        # Calculer la capacité
        new_capacity = self.calculate_capacity(
            base_capacity=capacity_source.weekly_capacity,
            mix_ratio=record.mix,
        )
        
        # Mise à jour conditionnelle (uniquement si nécessaire)
        old_capacity = record.calculated_weekly_capacity
        
        if old_capacity != new_capacity or not record.capacity_source:
            record.calculated_weekly_capacity = new_capacity
            record.capacity_source = capacity_source.source_name
            record.status = "ACTIVE" if new_capacity > 0 else "PRESOURCING"
            
            return True, (
                f"Capacité mise à jour: {old_capacity} → {new_capacity} "
                f"(source: {capacity_source.source_name})"
            )
        
        return True, "Capacité inchangée"
    
    def batch_update_capacities(
        self,
        records: List[CMFRecord],
        force_update: bool = False,
    ) -> Dict[int, Tuple[bool, str]]:
        """
        Met à jour les capacités pour plusieurs records.
        
        Returns:
            Dictionnaire {record_index: (success, message)}
        """
        results = {}
        
        for idx, record in enumerate(records):
            success, message = self.update_capacity_for_record(record, force_update)
            results[idx] = (success, message)
        
        return results
    
    def calculate_aggregate_capacity(
        self,
        records: List[CMFRecord],
        group_by_field: str = "part_number",
    ) -> pd.DataFrame:
        """
        Calcule la capacité agrégée par groupe.
        
        Args:
            records: Liste de records
            group_by_field: Champ de groupage
        
        Returns:
            DataFrame avec statistiques agrégées
        """
        data = []
        
        for record in records:
            if record.status != "PRESOURCING":
                data.append({
                    "group": getattr(record, group_by_field, ""),
                    "capacity": record.calculated_weekly_capacity,
                    "supplier": record.supplier_name,
                })
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Agrégation par groupe
        aggregated = df.groupby("group").agg({
            "capacity": ["sum", "mean", "count"],
            "supplier": lambda x: ", ".join(x.unique())
        }).round(2)
        
        return aggregated
    
    def get_capacity_gaps(
        self,
        records: List[CMFRecord],
    ) -> List[CMFRecord]:
        """
        Identifie les records en presourcing (gaps de capacité).
        
        Returns:
            Liste des records en presourcing
        """
        return [r for r in records if r.status == "PRESOURCING"]
    
    def get_capacity_summary(self, records: List[CMFRecord]) -> Dict:
        """Retourne un résumé des capacités"""
        active = [r for r in records if r.status == "ACTIVE"]
        presourcing = [r for r in records if r.status == "PRESOURCING"]
        
        total_capacity = sum(r.calculated_weekly_capacity for r in active)
        avg_capacity = (
            total_capacity / len(active) if active else 0
        )
        
        return {
            "total_active_records": len(active),
            "total_presourcing_records": len(presourcing),
            "total_capacity_parts_per_week": round(total_capacity, 2),
            "average_capacity_per_record": round(avg_capacity, 2),
            "presourcing_percentage": round(
                (len(presourcing) / len(records) * 100) if records else 0, 1
            ),
        }
    
    def assign_capacity_from_source_batch(
        self,
        cmf_records: List[CMFRecord],
        source_df: pd.DataFrame,
        source_name: str,
        excel_service,
        user: str,
        role: str,
        audit_service=None,
    ) -> Dict[str, any]:
        """
        Assigne la capacité ligne par ligne depuis un fichier source.
        
        Algorithme MÉTIER:
        1. Pour CHAQUE ligne du fichier source
        2. Extraire le Part Number
        3. SI Part Number vide ou "NEW" → skip
        4. SI Part Number match dans CMF → mettre à jour TOUS les records correspondants
        5. SINON → logger comme PRESOURCING, continuer
        
        Args:
            cmf_records: Liste des records CMF actuels
            source_df: DataFrame avec les données source (colonnes: PartNumber, WeeklyCapacity, Mix optionnel)
            source_name: Nom de la source (LTOS, GST, FETE, TKO, etc.)
            excel_service: Service Excel pour les mises à jour
            user: Utilisateur qui fait l'import
            role: Rôle de l'utilisateur
            audit_service: Service d'audit (optionnel)
        
        Returns:
            Dict avec résumé:
            {
                "success": bool,
                "source_lines_processed": int,
                "cmf_records_updated": int,
                "duplicates_handled": int,
                "part_numbers_not_found": int,
                "part_numbers_skipped": int,
                "errors": List[str],
                "presourcing_mismatches": List[Dict],
                "updated_records": List[Dict]
            }
        """
        results = {
            "success": True,
            "source_lines_processed": 0,
            "cmf_records_updated": 0,
            "duplicates_handled": 0,
            "part_numbers_not_found": 0,
            "part_numbers_skipped": 0,
            "errors": [],
            "presourcing_mismatches": [],
            "updated_records": [],
        }
        
        try:
            # Normaliser les colonnes du DataFrame source
            source_df.columns = [col.strip().lower() for col in source_df.columns]
            
            # Mapper les noms de colonnes possibles
            part_col = None
            capacity_col = None
            mix_col = None
            
            for col in source_df.columns:
                if col in ['partnumber', 'part_number', 'part #', 'pn']:
                    part_col = col
                elif col in ['weeklycapacity', 'weekly_capacity', 'capacity', 'cap']:
                    capacity_col = col
                elif col in ['mix', 'mix_ratio', 'mixratio']:
                    mix_col = col
            
            if not part_col or not capacity_col:
                results["success"] = False
                results["errors"].append(
                    f"Colonnes requises non trouvées. Attendu: PartNumber, WeeklyCapacity. "
                    f"Trouvé: {list(source_df.columns)}"
                )
                return results
            
            # Boucle sur chaque ligne source
            for idx, source_row in source_df.iterrows():
                results["source_lines_processed"] += 1
                
                try:
                    # Extraire Part Number
                    part_number = str(source_row[part_col]).strip() if source_row[part_col] else ""
                    
                    # Règle: ignorer les Part Numbers vides ou "NEW"
                    if not part_number or part_number.upper() == "NEW":
                        results["part_numbers_skipped"] += 1
                        continue
                    
                    # Chercher les records correspondants dans CMF
                    matching_records = [
                        r for r in cmf_records
                        if r.part_number and r.part_number.strip() == part_number
                    ]
                    
                    if not matching_records:
                        # Mismatch: Part Number non trouvé
                        results["part_numbers_not_found"] += 1
                        results["presourcing_mismatches"].append({
                            "source_row": idx + 1,
                            "part_number": part_number,
                            "reason": "Part Number non trouvé dans CMF",
                            "action": "À faire: Vérifier avec l'Acheteur"
                        })
                        continue
                    
                    # Gérer les doublons: mettre à jour TOUS les records correspondants
                    if len(matching_records) > 1:
                        results["duplicates_handled"] += len(matching_records) - 1
                    
                    # Extraire les données de capacité
                    try:
                        weekly_capacity = float(source_row[capacity_col])
                    except (ValueError, TypeError):
                        results["errors"].append(
                            f"Ligne {idx + 1}: WeeklyCapacity invalide: {source_row[capacity_col]}"
                        )
                        continue
                    
                    # Mix ratio (optionnel, défaut 1.0)
                    mix = 1.0
                    if mix_col:
                        try:
                            mix = float(source_row[mix_col])
                            mix = max(0.0, min(1.0, mix))  # Clamp 0-1
                        except (ValueError, TypeError):
                            mix = 1.0
                    
                    # Mettre à jour CHAQUE record correspondant
                    for record in matching_records:
                        old_capacity = record.calculated_weekly_capacity
                        old_source = record.capacity_source
                        
                        # Mettre à jour les champs
                        record.calculated_weekly_capacity = weekly_capacity
                        record.mix = mix
                        record.capacity_source = source_name
                        record.status = "ACTIVE" if weekly_capacity > 0 else "PRESOURCING"
                        
                        # Sauvegarder dans Excel
                        if excel_service.update_cmf_record(record):
                            results["cmf_records_updated"] += 1
                            
                            # Tracker pour audit
                            update_detail = {
                                "row_id": record.row_id,
                                "part_number": part_number,
                                "old_capacity": old_capacity,
                                "new_capacity": weekly_capacity,
                                "old_source": old_source,
                                "new_source": source_name,
                                "mix": mix,
                            }
                            results["updated_records"].append(update_detail)
                            
                            # Journaliser si audit_service disponible
                            if audit_service:
                                try:
                                    audit_service.log_action(
                                        action="CAPACITY_BATCH_ASSIGNED",
                                        user=user,
                                        role=role,
                                        table="CMF",
                                        record_id=record.row_id,
                                        details=f"Batch import {source_name}: {old_capacity}→{weekly_capacity} parts/week"
                                    )
                                except Exception as e:
                                    results["errors"].append(f"Erreur audit ligne {idx + 1}: {str(e)}")
                        else:
                            results["errors"].append(
                                f"Ligne {idx + 1} ({part_number}): Erreur sauvegarde Excel"
                            )
                
                except Exception as e:
                    results["errors"].append(f"Ligne {idx + 1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Erreur traitement batch: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results
