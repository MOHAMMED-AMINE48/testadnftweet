"""
Service de logging et d'audit.
Journalise toutes les modifications dans une base centralisée.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from models.cmf_schema import AuditLog
from config.settings import LOG_FILE, LOG_DIR


class AuditService:
    """Service centralisé pour l'audit et la traçabilité"""
    
    def __init__(self, log_file: Path = LOG_FILE):
        """Initialise le service de logging"""
        self.log_file = log_file
        
        # Configurer le logger Python standard
        self.logger = logging.getLogger("CMF_AUDIT")
        self.logger.setLevel(logging.INFO)
        
        # Handler fichier
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logs = []
    
    def log_action(
        self,
        action: str,
        user: str,
        role: str,
        table: str,
        record_id: Optional[int] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: str = ""
    ) -> AuditLog:
        """
        Enregistre une action d'audit
        
        Args:
            action: Type d'action (CREATE, UPDATE, DELETE, IMPORT)
            user: Utilisateur ayant effectué l'action
            role: Rôle de l'utilisateur
            table: Table affectée
            record_id: ID du record affecté (optionnel)
            field_name: Nom du champ modifié (optionnel)
            old_value: Ancienne valeur (optionnel)
            new_value: Nouvelle valeur (optionnel)
            details: Détails supplémentaires
            
        Returns:
            AuditLog: L'enregistrement d'audit créé
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = AuditLog(
            timestamp=timestamp,
            user=user,
            role=role,
            action=action,
            table=table,
            record_id=record_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            details=details,
        )
        
        # Enregistrer dans le fichier log
        log_message = self._format_log_message(log_entry)
        self.logger.info(log_message)
        
        self.logs.append(log_entry)
        
        return log_entry
    
    @staticmethod
    def _format_log_message(log_entry: AuditLog) -> str:
        """Formate un message de log"""
        msg = f"[{log_entry.action}] {log_entry.table}"
        
        if log_entry.record_id:
            msg += f" (ID={log_entry.record_id})"
        
        if log_entry.field_name:
            msg += f" | [{log_entry.field_name}] {log_entry.old_value} → {log_entry.new_value}"
        
        if log_entry.details:
            msg += f" | {log_entry.details}"
        
        msg += f" | User: {log_entry.user} ({log_entry.role})"
        
        return msg
    
    def log_import(
        self,
        source_name: str,
        total_records: int,
        imported_records: int,
        user: str,
        role: str,
        details: str = ""
    ):
        """Enregistre un import de source de capacité"""
        self.log_action(
            action="IMPORT",
            user=user,
            role=role,
            table=source_name,
            details=f"Importé {imported_records}/{total_records} records. {details}",
        )
    
    def log_calculation(
        self,
        part_number: str,
        capacity_source: str,
        base_capacity: float,
        mix_ratio: float,
        final_capacity: float,
        user: str,
        role: str,
    ):
        """Enregistre un calcul de capacité"""
        self.log_action(
            action="CALCULATE",
            user=user,
            role=role,
            table="CMF",
            details=(
                f"Part:{part_number} Source:{capacity_source} "
                f"Base:{base_capacity} Mix:{mix_ratio} → Final:{final_capacity}"
            ),
        )
    
    def get_logs_for_record(self, record_id: int) -> list[AuditLog]:
        """Récupère tous les logs d'un record"""
        return [log for log in self.logs if log.record_id == record_id]
    
    def get_logs_for_user(self, user: str) -> list[AuditLog]:
        """Récupère tous les logs d'un utilisateur"""
        return [log for log in self.logs if log.user == user]
    
    def get_logs_for_field(self, table: str, field_name: str) -> list[AuditLog]:
        """Récupère l'historique de modifications d'un champ"""
        return [
            log for log in self.logs
            if log.table == table and log.field_name == field_name
        ]
    
    def export_logs_to_json(self, output_file: Path) -> None:
        """Exporte les logs en JSON"""
        logs_data = [log.to_dict() for log in self.logs]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, indent=2, ensure_ascii=False)
    
    def clear_old_logs(self, days: int = 90) -> int:
        """
        Supprime les logs de plus de N jours.
        Retourne le nombre de logs supprimés.
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.logs)
        
        self.logs = [
            log for log in self.logs
            if datetime.fromisoformat(log.timestamp) > cutoff_date
        ]
        
        return initial_count - len(self.logs)


# Instance globale du service d'audit
_audit_service = None


def get_audit_service() -> AuditService:
    """Retourne l'instance globale du service d'audit (Singleton)"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
