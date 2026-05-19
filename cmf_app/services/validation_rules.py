"""
Service de validation des données.
Implémente toutes les règles métier et validations.
"""

from typing import Tuple, List
import re

from models.cmf_schema import CMFRecord, ValidationResult, CapacitySource
from config.settings import VALIDATION_RULES, CAPACITY_SOURCES


class ValidationRules:
    """Classe statique avec toutes les règles de validation en métier"""
    
    @staticmethod
    def validate_cmf_record(record: CMFRecord) -> ValidationResult:
        """
        Valide un enregistrement CMF selon les règles métier.
        
        Règles:
        - Partname obligatoire
        - Si PartNumber vide ou "NEW" → presourcing
        - Quantity > 0
        - Mix ratio entre 0 et 1
        - CapacitySource doit être dans la liste autorisée
        """
        result = ValidationResult(is_valid=True)
        
        # Validation Acheteur
        if not record.partname or record.partname.strip() == "":
            result.add_error("Partname est obligatoire")
        
        if record.quantity <= 0 and record.quantity != 0:
            result.add_error(f"Quantity doit être positif (reçu: {record.quantity})")
        
        # Validation Part Number
        if not record.part_number or record.part_number.strip() == "" or record.part_number == "NEW":
            result.add_warning("Part Number vide ou 'NEW' → le record sera en PRESOURCING")
        
        # Validation Capacity Manager
        if record.mix < VALIDATION_RULES["min_mix_ratio"] or record.mix > VALIDATION_RULES["max_mix_ratio"]:
            result.add_error(
                f"Mix doit être entre {VALIDATION_RULES['min_mix_ratio']} et {VALIDATION_RULES['max_mix_ratio']}"
            )
        
        if record.capacity_source and record.capacity_source not in CAPACITY_SOURCES:
            result.add_error(f"CapacitySource invalide: {record.capacity_source}")
        
        # Validation des dates (format simple check)
        date_fields = [
            record.cat1_forecasted_date,
            record.cat2_forecasted_date,
            record.cat3_forecasted_date,
        ]
        for date_field in date_fields:
            if date_field and not ValidationRules._is_valid_date(date_field):
                result.add_warning(f"Format de date potentiellement invalide: {date_field}")
        
        # Validation des évaluations CAT
        valid_evaluations = ["G", "O", "R", ""]
        for eval_field in [record.cat1_evaluation, record.cat2_evaluation, record.cat3_evaluation]:
            if eval_field and eval_field not in valid_evaluations:
                result.add_error(f"Évaluation invalide (doit être G/O/R): {eval_field}")
        
        return result
    
    @staticmethod
    def validate_capacity_source(source: CapacitySource) -> ValidationResult:
        """Valide une source de capacité"""
        result = ValidationResult(is_valid=True)
        
        if not source.part_number or source.part_number.strip() == "":
            result.add_error("PartNumber obligatoire dans la source")
        
        if source.weekly_capacity < VALIDATION_RULES["min_capacity"]:
            result.add_error(
                f"Weekly capacity insuffisant: {source.weekly_capacity} "
                f"(min: {VALIDATION_RULES['min_capacity']})"
            )
        
        if source.mix_ratio < 0 or source.mix_ratio > 1.0:
            result.add_error("Mix ratio doit être entre 0 et 1")
        
        if source.source_name not in CAPACITY_SOURCES:
            result.add_error(f"Source invalide: {source.source_name}")
        
        return result
    
    @staticmethod
    def check_duplicate_part_numbers(
        part_number: str,
        existing_records: List[CMFRecord]
    ) -> Tuple[bool, List[int]]:
        """
        Vérifie les doublons de Part Number.
        
        Les Part Numbers peuvent être dupliqués selon les règles métier.
        Cette fonction retourne les indices des records avec le même Part Number.
        
        Returns:
            Tuple: (has_duplicates, list of matched record indices)
        """
        if not part_number or part_number == "NEW":
            return False, []
        
        matched_indices = [
            i for i, record in enumerate(existing_records)
            if record.part_number == part_number
        ]
        
        has_duplicates = len(matched_indices) > 0
        
        return has_duplicates, matched_indices
    
    @staticmethod
    def is_presourcing_record(record: CMFRecord) -> bool:
        """Détermine si un record est en presourcing"""
        return (
            not record.part_number
            or record.part_number.strip() == ""
            or record.part_number == "NEW"
            or not record.capacity_source
            or record.calculated_weekly_capacity <= 0
        )
    
    @staticmethod
    def validate_buyer_permissions(fields_to_update: dict) -> ValidationResult:
        """Valide que l'Acheteur n'essaie de modifier que ses champs autorisés"""
        from config.settings import ROLE_PERMISSIONS, UserRole
        
        result = ValidationResult(is_valid=True)
        allowed_fields = set(ROLE_PERMISSIONS[UserRole.BUYER]["write"])
        
        for field in fields_to_update.keys():
            if field not in allowed_fields:
                result.add_error(
                    f"Acheteur n'est pas autorisé à modifier: {field}"
                )
        
        return result
    
    @staticmethod
    def validate_capacity_manager_permissions(fields_to_update: dict) -> ValidationResult:
        """Valide que le Capacity Manager n'essaie de modifier que ses champs"""
        from config.settings import ROLE_PERMISSIONS, UserRole
        
        result = ValidationResult(is_valid=True)
        allowed_fields = set(ROLE_PERMISSIONS[UserRole.CAPACITY_MANAGER]["write"])
        
        for field in fields_to_update.keys():
            if field not in allowed_fields:
                result.add_error(
                    f"Capacity Manager n'est pas autorisé à modifier: {field}"
                )
        
        return result
    
    @staticmethod
    def validate_sqd_permissions(fields_to_update: dict) -> ValidationResult:
        """Valide que SQD n'essaie de modifier que ses champs"""
        from config.settings import ROLE_PERMISSIONS, UserRole
        
        result = ValidationResult(is_valid=True)
        allowed_fields = set(ROLE_PERMISSIONS[UserRole.SQD]["write"])
        
        for field in fields_to_update.keys():
            if field not in allowed_fields:
                result.add_error(
                    f"SQD n'est pas autorisé à modifier: {field}"
                )
        
        return result
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Vérifie si une date est au format valide (simplifié)"""
        if not date_str:
            return True
        
        # Formats acceptés: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
        ]
        
        return any(re.match(pattern, date_str) for pattern in patterns)


def validate_record(record: CMFRecord) -> ValidationResult:
    """Fonction raccourcie pour valider un record"""
    return ValidationRules.validate_cmf_record(record)


def validate_source(source: CapacitySource) -> ValidationResult:
    """Fonction raccourcie pour valider une source"""
    return ValidationRules.validate_capacity_source(source)
