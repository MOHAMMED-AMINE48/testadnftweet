"""
Règles métier pour la gestion des capacités - Capacity Manager.
Validation et vérification de la cohérence entre données Acheteur et Capacity Manager.
"""

from typing import Dict, Any, List, Tuple
from models.cmf_schema import CMFRecord, CapacitySource


class CapacityAssignmentRules:
    """
    Règles métier strictes pour l'assignation de capacité par le Capacity Manager.
    
    RÈGLE CLÉ (non négociable):
    Le Capacity Manager ne peut assigner automatiquement une capacité QUE si:
    - Part Numbers sont STRICTEMENT identiques entre données Acheteur et source de capacité
    
    Sinon: assignation automatique bloquée, saisie manuelle obligatoire
    """
    
    @staticmethod
    def is_capacity_assignment_allowed(
        cmf_record: CMFRecord,
        capacity_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Vérifie si l'assignation de capacité automatique est autorisée.
        
        Args:
            cmf_record: Record CMF de l'Acheteur
            capacity_data: Données de la source de capacité
                          (structure: {'part_number': '...', 'supplier_name': '...', 'weekly_capacity': 100})
        
        Returns:
            Tuple (is_allowed: bool, reason: str)
            - (True, "") si assignation automatique autorisée
            - (False, "message d'erreur") si assignation automatique bloquée
        """
        
        # ===== VALIDATION 1: Part Number identique =====
        buyer_part_number = (cmf_record.part_number or "").strip().upper()
        capacity_part_number = (capacity_data.get('part_number') or "").strip().upper()
        
        if not buyer_part_number or not capacity_part_number:
            return False, " Part Number manquant (Acheteur ou source)"
        
        if buyer_part_number != capacity_part_number:
            return (
                False, 
                f" Mismatch Part Number:\n"
                f"   Acheteur: {buyer_part_number}\n"
                f"   Source: {capacity_part_number}\n"
                f"→ Saisie manuelle obligatoire"
            )
        
        # ===== VALIDATION 2: Fournisseur (optionnel mais recommandé) =====
        buyer_supplier = (cmf_record.supplier_name or "").strip().upper()
        capacity_supplier = (capacity_data.get('supplier_name') or "").strip().upper()
        
        if buyer_supplier and capacity_supplier and buyer_supplier != capacity_supplier:
            # Avertissement mais pas bloquant
            return (
                True,
                f" ATTENTION: Fournisseur différent\n"
                f"   Acheteur: {buyer_supplier}\n"
                f"   Source: {capacity_supplier}\n"
                f"→ Vérifiez avant validation"
            )
        
        # ===== VALIDATION 3: Capacité valide =====
        try:
            weekly_capacity = float(capacity_data.get('weekly_capacity', 0))
            if weekly_capacity <= 0:
                return (
                    False,
                    f" Capacité invalide: {weekly_capacity}\n"
                    f"→ La capacité doit être > 0"
                )
        except (ValueError, TypeError):
            return (
                False,
                f" Capacité non numérique: {capacity_data.get('weekly_capacity')}"
            )
        
        # ===== TOUS LES CONTRÔLES PASSÉS =====
        return True, " Assignation automatique autorisée"
    
    @staticmethod
    def validate_capacity_source_compatibility(
        cmf_records: List[CMFRecord],
        capacity_sources: List[Dict[str, Any]],
        strict_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Valide la compatibilité entre un batch de records CMF et des sources de capacité.
        
        Args:
            cmf_records: Liste de records CMF de l'Acheteur
            capacity_sources: Liste de données de capacité à importer
            strict_mode: Si True, rejette les incompatibilités; si False, alerte seulement
        
        Returns:
            Dict avec:
            - 'all_compatible': bool - Tous les records sont compatibles?
            - 'matches': List - Records/sources qui matchent
            - 'mismatches': List - Records/sources qui ne matchent pas
            - 'warnings': List - Avertissements
            - 'errors': List - Erreurs (si strict_mode)
        """
        result = {
            'all_compatible': True,
            'matches': [],
            'mismatches': [],
            'warnings': [],
            'errors': [],
            'auto_assignable_count': 0,
            'manual_required_count': 0,
        }
        
        # Construire un mapping des part_numbers
        cmf_by_part = {}
        for record in cmf_records:
            part_num = (record.part_number or "").strip().upper()
            if part_num and part_num != "NEW":
                cmf_by_part[part_num] = record
        
        # Vérifier chaque source
        for capacity_item in capacity_sources:
            capacity_part = (capacity_item.get('part_number') or "").strip().upper()
            
            if not capacity_part:
                result['warnings'].append(
                    f" Source sans Part Number détectée: {capacity_item}"
                )
                result['mismatches'].append(capacity_item)
                continue
            
            if capacity_part in cmf_by_part:
                # C'est un match!
                cmf_record = cmf_by_part[capacity_part]
                is_allowed, reason = CapacityAssignmentRules.is_capacity_assignment_allowed(
                    cmf_record, capacity_item
                )
                
                if is_allowed:
                    result['matches'].append({
                        'cmf_record': cmf_record,
                        'capacity_data': capacity_item,
                        'status': 'AUTO_ASSIGNABLE',
                        'message': reason
                    })
                    result['auto_assignable_count'] += 1
                else:
                    result['mismatches'].append({
                        'cmf_record': cmf_record,
                        'capacity_data': capacity_item,
                        'status': 'MANUAL_REQUIRED',
                        'message': reason
                    })
                    result['manual_required_count'] += 1
                    result['warnings'].append(reason)
            else:
                # Part Number de la source n'existe pas dans CMF
                result['mismatches'].append({
                    'capacity_data': capacity_item,
                    'status': 'NOT_FOUND_IN_CMF',
                    'message': f" Part Number {capacity_part} non trouvé dans CMF Acheteur"
                })
                result['manual_required_count'] += 1
                result['warnings'].append(
                    f" Source Part Number {capacity_part} n'a pas de correspondance dans CMF"
                )
        
        # Déterminer la compatibilité globale
        if strict_mode:
            result['all_compatible'] = len(result['mismatches']) == 0
        else:
            result['all_compatible'] = len(result['errors']) == 0
        
        return result
    
    @staticmethod
    def get_field_conflicts(
        cmf_record: CMFRecord,
        updates: Dict[str, Any]
    ) -> List[str]:
        """
        Détecte les champs qui seraient modifiés par une assignation de capacité.
        
        Args:
            cmf_record: Record existant
            updates: Nouvelles données de capacité
        
        Returns:
            Liste des champs qui changeraient
        """
        conflicts = []
        
        # Mapping des champs qui peuvent être affectés
        field_map = {
            'GST': 'gst',
            'Mix': 'mix',
            'CalculatedWeeklyCapacity': 'calculated_weekly_capacity',
        }
        
        for excel_field, model_field in field_map.items():
            old_value = getattr(cmf_record, model_field, None)
            new_value = updates.get(excel_field)
            
            if old_value != new_value:
                conflicts.append(
                    f"🔄 {excel_field}: {old_value} → {new_value}"
                )
        
        return conflicts


# ===== EXPORT =====
def validate_capacity_assignment(
    cmf_record: CMFRecord,
    capacity_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """Alias pratique pour is_capacity_assignment_allowed"""
    return CapacityAssignmentRules.is_capacity_assignment_allowed(cmf_record, capacity_data)
