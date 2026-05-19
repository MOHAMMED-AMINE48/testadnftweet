"""
Couche repository abstraite pour accès aux données.
Permet le remplacement Excel → SQL sans modifier le reste du code.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.cmf_schema import CMFRecord, CapacitySource, AuditLog


class IRepository(ABC):
    """Interface abstraite: tous les repositories doivent l'implémenter"""
    
    @abstractmethod
    def get_all_cmf_records(self) -> List[CMFRecord]:
        """Récupère tous les records CMF"""
        pass
    
    @abstractmethod
    def get_cmf_record_by_id(self, record_id: int) -> Optional[CMFRecord]:
        """Récupère un record CMF par ID"""
        pass
    
    @abstractmethod
    def create_cmf_record(self, record: CMFRecord) -> int:
        """Crée un nouveau record et retourne son ID"""
        pass
    
    @abstractmethod
    def update_cmf_record(self, record: CMFRecord) -> bool:
        """Met à jour un record existant"""
        pass
    
    @abstractmethod
    def delete_cmf_record(self, record_id: int) -> bool:
        """Supprime un record"""
        pass
    
    @abstractmethod
    def get_capacity_sources(self, source_name: str) -> List[CapacitySource]:
        """Récupère toutes les sources d'une pile"""
        pass
    
    @abstractmethod
    def add_capacity_source(self, source: CapacitySource) -> bool:
        """Ajoute une source de capacité"""
        pass
    
    @abstractmethod
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[AuditLog]:
        """Récupère les logs d'audit avec filtres optionnels"""
        pass
    
    @abstractmethod
    def add_audit_log(self, log: AuditLog) -> bool:
        """Ajoute une entrée d'audit"""
        pass


class ExcelRepository(IRepository):
    """
    Implémentation Excel du repository.
    Interface centralisée pour lire/écrire le fichier Excel.
    """
    
    def __init__(self, file_path: str):
        """
        Initialise le repository Excel.
        
        Args:
            file_path: Chemin vers CMF_MASTER.xlsx
        """
        self.file_path = file_path
        self._excel_service = None  # Sera injecté via setter
    
    def set_excel_service(self, service):
        """Injecte le service Excel"""
        self._excel_service = service
    
    def _check_service(self):
        """Vérifie que le service Excel est configuré"""
        if not self._excel_service:
            raise RuntimeError("ExcelService not initialized!")
    
    def get_all_cmf_records(self) -> List[CMFRecord]:
        """Récupère tous les records CMF"""
        self._check_service()
        return self._excel_service.read_cmf_records()
    
    def get_cmf_record_by_id(self, record_id: int) -> Optional[CMFRecord]:
        """Récupère un record par ID"""
        self._check_service()
        records = self._excel_service.read_cmf_records()
        return next((r for r in records if r.row_id == record_id), None)
    
    def create_cmf_record(self, record: CMFRecord) -> int:
        """Crée un nouvel enregistrement"""
        self._check_service()
        record.last_updated = datetime.now().isoformat()
        return self._excel_service.write_cmf_record(record)
    
    def update_cmf_record(self, record: CMFRecord) -> bool:
        """Met à jour un enregistrement"""
        self._check_service()
        record.last_updated = datetime.now().isoformat()
        return self._excel_service.update_cmf_record(record)
    
    def delete_cmf_record(self, record_id: int) -> bool:
        """Marque un record comme inactif (soft delete)"""
        self._check_service()
        record = self.get_cmf_record_by_id(record_id)
        if not record:
            return False
        record.status = "INACTIVE"
        record.last_updated = datetime.now().isoformat()
        return self.update_cmf_record(record)
    
    def get_capacity_sources(self, source_name: str) -> List[CapacitySource]:
        """Récupère les sources de capacité"""
        self._check_service()
        return self._excel_service.read_capacity_sources(source_name)
    
    def add_capacity_source(self, source: CapacitySource) -> bool:
        """Ajoute une source"""
        self._check_service()
        return self._excel_service.write_capacity_source(source)
    
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[AuditLog]:
        """Récupère les logs d'audit"""
        self._check_service()
        return self._excel_service.read_audit_logs(filters)
    
    def add_audit_log(self, log: AuditLog) -> bool:
        """Ajoute un log d'audit"""
        self._check_service()
        return self._excel_service.write_audit_log(log)


class SQLRepository(IRepository):
    """
    Implémentation SQL pour future migration.
    Connecte PostgreSQL / Supabase pour les données.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialise le repository SQL.
        
        Args:
            connection_string: String de connexion PostgreSQL
        """
        self.connection_string = connection_string
        self._connection = None
    
    def connect(self):
        """Se connecte à la base de données"""
        # Sera implémenté lors de la migration SQL
        raise NotImplementedError("SQL Repository configured for future use")
    
    def get_all_cmf_records(self) -> List[CMFRecord]:
        """Récupère tous les records de la DB"""
        raise NotImplementedError()
    
    def get_cmf_record_by_id(self, record_id: int) -> Optional[CMFRecord]:
        raise NotImplementedError()
    
    def create_cmf_record(self, record: CMFRecord) -> int:
        raise NotImplementedError()
    
    def update_cmf_record(self, record: CMFRecord) -> bool:
        raise NotImplementedError()
    
    def delete_cmf_record(self, record_id: int) -> bool:
        raise NotImplementedError()
    
    def get_capacity_sources(self, source_name: str) -> List[CapacitySource]:
        raise NotImplementedError()
    
    def add_capacity_source(self, source: CapacitySource) -> bool:
        raise NotImplementedError()
    
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[AuditLog]:
        raise NotImplementedError()
    
    def add_audit_log(self, log: AuditLog) -> bool:
        raise NotImplementedError()


class RepositoryFactory:
    """Factory pour créer le bon type de repository"""
    
    @staticmethod
    def create_repository(repo_type: str, **kwargs):
        """
        Crée un repository du type spécifié.
        
        Args:
            repo_type: "sqlite", "excel" ou "sql"
            **kwargs: Paramètres spécifiques au type
        
        Returns:
            Une instance du repository
        """
        if repo_type == "sqlite":
            from repositories.cmf_repository_sqlite import CMFRepository
            return CMFRepository()
        
        elif repo_type == "excel":
            repo = ExcelRepository(kwargs.get("file_path", "CMF_MASTER.xlsx"))
            if "excel_service" in kwargs:
                repo.set_excel_service(kwargs["excel_service"])
            return repo
        
        elif repo_type == "sql":
            return SQLRepository(kwargs.get("connection_string", ""))
        
        else:
            raise ValueError(f"Type de repository inconnu: {repo_type}. Utilisez 'sqlite', 'excel' ou 'sql'")
