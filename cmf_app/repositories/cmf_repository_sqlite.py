"""
Repository SQLite pour la gestion des Records CMF.
Gère la persitance des données Buyer, Capacity Manager et SQD.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

from db_sqlite import (
    get_connection,
    close_connection,
    ensure_cmf_records_schema,
    get_columns_registry_map,
    resolve_db_name,
    to_db_name,
)
from utils.encoding_handler import clean_record

try:
    from services.master_schema import MASTER_COLUMNS_ORDER
except Exception:
    MASTER_COLUMNS_ORDER = []


_SYSTEM_FIELDS = {"id", "project_id", "last_updated", "updated_by"}


@dataclass
class CMFRecord:
    """
    Modèle de données pour une ligne CMF (record).
    """
    id: int
    project_id: int
    
    # Données Buyer (APQP/Part Number)
    apqp: Optional[str] = None
    part_name: Optional[str] = None
    part_number: Optional[str] = None
    use_case: Optional[str] = None
    commodity: Optional[str] = None
    quantity: float = 0.0
    mix: float = 1.0
    supplier_name: Optional[str] = None
    manufacturing_cofor: Optional[str] = None
    production_location: Optional[str] = None
    buyer: Optional[str] = None
    purchasing_manager: Optional[str] = None
    gm: Optional[str] = None
    sque: Optional[str] = None
    
    # Données Capacity Manager
    scr: Optional[str] = None
    link_to_doc_info: Optional[str] = None
    gst_no: Optional[str] = None
    capacity_source: Optional[str] = None
    calculated_weekly_capacity: float = 0.0
    cm_comment: Optional[str] = None
    
    # Données SQD
    weekly_capacity_to_measure: float = 0.0
    k9_sck: Optional[str] = None
    cat1_forecasted_date: Optional[str] = None
    cat2_forecasted_date: Optional[str] = None
    cat3_forecasted_date: Optional[str] = None
    cat1_type: Optional[str] = None
    cat2_type: Optional[str] = None
    cat3_type: Optional[str] = None
    weekly_capacity_measured: float = 0.0
    estimated_target: float = 0.0
    cat1_evaluation: Optional[str] = None
    cat2_evaluation: Optional[str] = None
    cat3_evaluation: Optional[str] = None
    shared_folder: Optional[str] = None
    sqd_comment: Optional[str] = None
    sque_team: Optional[str] = None
    
    # Métadonnées système
    status: str = "PRESOURCING"
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "CMFRecord":
        """Crée une instance CMFRecord à partir d'une ligne SQLite."""
        data = dict(row)
        # Créer l'instance avec tous les champs disponibles
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return asdict(self)


class CMFRepository:
    """
    Repository pour gérer les records CMF en SQLite.
    """

    def _prepare_record_data(self, data: Dict[str, Any], existing_columns: set[str]) -> tuple[Dict[str, Any], List[str]]:
        """Mappe les clés display -> db_name et filtre les colonnes absentes."""
        registry = get_columns_registry_map()
        normalized: Dict[str, Any] = {}
        warnings: List[str] = []

        for key, value in data.items():
            if key in _SYSTEM_FIELDS:
                continue

            db_key = key
            if db_key not in existing_columns:
                db_key = registry.get(key, resolve_db_name(key))

            if db_key in _SYSTEM_FIELDS:
                continue

            if db_key not in existing_columns:
                warnings.append(f"Skipped column '{key}' -> '{db_key}' (not in cmf_records)")
                continue

            normalized[db_key] = value

        return normalized, warnings

    def get_records_for_project(self, project_id: int, status: Optional[str] = None) -> List[CMFRecord]:
        """
        Retourne les records CMF d'un projet.
        
        Args:
            project_id: ID du projet
            status: Filtre optionnel par statut (PRESOURCING, ACTIVE, etc.)
            
        Returns:
            Liste des records CMF
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            if status:
                cur.execute("""
                    SELECT * FROM cmf_records
                    WHERE project_id = ? AND status = ?
                    ORDER BY id
                """, (project_id, status))
            else:
                cur.execute("""
                    SELECT * FROM cmf_records
                    WHERE project_id = ?
                    ORDER BY id
                """, (project_id,))
            
            rows = cur.fetchall()
            return [CMFRecord.from_row(row) for row in rows]
        finally:
            close_connection(conn)

    def get_record_by_id(self, record_id: int) -> Optional[CMFRecord]:
        """
        Retourne un record par son ID.
        
        Args:
            record_id: ID du record
            
        Returns:
            Le record, ou None s'il n'existe pas
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cmf_records WHERE id = ?", (record_id,))
            row = cur.fetchone()
            return CMFRecord.from_row(row) if row else None
        finally:
            close_connection(conn)

    def get_records_by_part_number(self, project_id: int, part_number: str) -> List[CMFRecord]:
        """
        Retourne les records pour un part_number donné dans un projet.
        
        Args:
            project_id: ID du projet
            part_number: Numéro de pièce
            
        Returns:
            Liste des records correspondants
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM cmf_records
                WHERE project_id = ? AND part_number = ?
                ORDER BY id
            """, (project_id, part_number))
            
            rows = cur.fetchall()
            return [CMFRecord.from_row(row) for row in rows]
        finally:
            close_connection(conn)

    def get_records_by_apqp_and_part_number(
        self, project_id: int, apqp: str, part_number: str
    ) -> List[CMFRecord]:
        """
        Retourne les records correspondant à APQP + Part Number.
        
        Args:
            project_id: ID du projet
            apqp: APQP
            part_number: Numéro de pièce
            
        Returns:
            Liste des records correspondants
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM cmf_records
                WHERE project_id = ? AND apqp = ? AND part_number = ?
                ORDER BY id
            """, (project_id, apqp, part_number))
            
            rows = cur.fetchall()
            return [CMFRecord.from_row(row) for row in rows]
        finally:
            close_connection(conn)

    def create_record(
        self,
        project_id: int,
        data: Dict[str, Any],
        updated_by: str,
        status: str = "PRESOURCING"
    ) -> CMFRecord:
        """
        Crée un nouveau record CMF (avec support des colonnes personnalisées).
        
        Args:
            project_id: ID du projet
            data: Dictionnaire des données du record
            updated_by: Utilisateur créant le record
            status: Statut initial (par défaut: PRESOURCING)
            
        Returns:
            Le record créé
        """
        conn = get_connection()
        try:
            if MASTER_COLUMNS_ORDER:
                migration_report = ensure_cmf_records_schema(MASTER_COLUMNS_ORDER)
            else:
                migration_report = {"success": True, "added_columns": [], "existing_columns": [], "skipped_columns": [], "errors": []}

            # ✅ Nettoyer les données pour éviter les problèmes d'encodage
            data = clean_record(data)
            
            # Déterminer le statut en fonction du part_number
            part_number = data.get("part_number", "").strip()
            if part_number and part_number.upper() != "NEW":
                status = "ACTIVE"

            cur = conn.cursor()
            cur.execute("PRAGMA table_info(cmf_records)")
            existing_columns = {row[1] for row in cur.fetchall()}

            normalized_data, warnings = self._prepare_record_data(data, existing_columns)

            self.last_operation_report = {
                "success": True,
                "warnings": warnings,
                "migration_report": migration_report,
                "skipped_columns": warnings,
                "errors": [],
            }

            # Préparer les colonnes système
            columns = ["project_id", "status", "updated_by", "last_updated"]
            values = [project_id, status, updated_by, datetime.now().isoformat()]

            # Ajouter uniquement les colonnes réellement présentes dans cmf_records
            for key, value in normalized_data.items():
                columns.append(key)
                values.append(value)

            # Exécuter l'insertion
            placeholders = ", ".join(["?"] * len(columns))
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO cmf_records ({', '.join([f'\"{col.replace(chr(34), "")}\"' for col in columns])}) VALUES ({placeholders})",
                values
            )
            conn.commit()
            record_id = cur.lastrowid

            return self.get_record_by_id(record_id)
        finally:
            close_connection(conn)

    def update_record(self, record_id: int, data: Dict[str, Any], updated_by: str) -> Optional[CMFRecord]:
        """
        Met à jour un record CMF (avec support des colonnes personnalisées).
        
        Args:
            record_id: ID du record à mettre à jour
            data: Dictionnaire des champs à mettre à jour
            updated_by: Utilisateur effectuant la mise à jour
            
        Returns:
            Le record mis à jour, ou None s'il n'existe pas
        """
        # Vérifier que le record existe
        existing = self.get_record_by_id(record_id)
        if not existing:
            return None

        # ✅ Nettoyer les données pour éviter les problèmes d'encodage
        data = clean_record(data)

        if MASTER_COLUMNS_ORDER:
            migration_report = ensure_cmf_records_schema(MASTER_COLUMNS_ORDER)
        else:
            migration_report = {"success": True, "added_columns": [], "existing_columns": [], "skipped_columns": [], "errors": []}

        conn_check = get_connection()
        try:
            cur = conn_check.cursor()
            cur.execute("PRAGMA table_info(cmf_records)")
            existing_columns = {row[1] for row in cur.fetchall()}
        finally:
            close_connection(conn_check)

        normalized_data, warnings = self._prepare_record_data(data, existing_columns)

        self.last_operation_report = {
            "success": True,
            "warnings": warnings,
            "migration_report": migration_report,
            "skipped_columns": warnings,
            "errors": [],
        }

        update_data = dict(normalized_data)
        
        if not update_data:
            return existing

        # Ajouter les métadonnées de mise à jour
        update_data["updated_by"] = updated_by
        update_data["last_updated"] = datetime.now().isoformat()

        # Construire la requête UPDATE
        set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [record_id]

        conn = get_connection()
        try:
            cur = conn.cursor()
            set_clause = ", ".join([f'\"{k.replace(chr(34), "")}\" = ?' for k in update_data.keys()])
            cur.execute(
                f"UPDATE cmf_records SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return self.get_record_by_id(record_id)
        finally:
            close_connection(conn)

    def delete_record(self, record_id: int) -> bool:
        """
        Supprime un record CMF.
        
        Args:
            record_id: ID du record à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM cmf_records WHERE id = ?", (record_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            close_connection(conn)

    def count_records_for_project(self, project_id: int, status: Optional[str] = None) -> int:
        """
        Compte les records d'un projet.
        
        Args:
            project_id: ID du projet
            status: Filtre optionnel par statut
            
        Returns:
            Nombre de records
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            if status:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cmf_records
                    WHERE project_id = ? AND status = ?
                """, (project_id, status))
            else:
                cur.execute("""
                    SELECT COUNT(*) as count FROM cmf_records
                    WHERE project_id = ?
                """, (project_id,))
            
            row = cur.fetchone()
            return row["count"] if row else 0
        finally:
            close_connection(conn)

    def bulk_create_records(
        self,
        project_id: int,
        records_data: List[Dict[str, Any]],
        updated_by: str
    ) -> List[CMFRecord]:
        """
        Crée plusieurs records CMF en une seule opération (batch).
        
        Args:
            project_id: ID du projet
            records_data: Liste de dictionnaires de données
            updated_by: Utilisateur effectuant l'insertion
            
        Returns:
            Liste des records créés
        """
        created_records = []
        for data in records_data:
            record = self.create_record(project_id, data, updated_by)
            if record:
                created_records.append(record)
        return created_records

    def get_records_raw(self, project_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retourne les records RAW (dictionnaires) avec TOUS les champs de la base.
        Inclut les colonnes personnalisées qui ne sont pas dans CMFRecord.
        
        Args:
            project_id: ID du projet
            status: Filtre optionnel par statut
            
        Returns:
            Liste de dictionnaires avec tous les champs de la base de données
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            if status:
                cur.execute("""
                    SELECT * FROM cmf_records
                    WHERE project_id = ? AND status = ?
                    ORDER BY id
                """, (project_id, status))
            else:
                cur.execute("""
                    SELECT * FROM cmf_records
                    WHERE project_id = ?
                    ORDER BY id
                """, (project_id,))
            
            rows = cur.fetchall()
            # Convertir les Row objects en dictionnaires
            return [dict(row) for row in rows]
        finally:
            close_connection(conn)

    def get_cross_project_part_number_view(self) -> List[Dict[str, Any]]:
        """
        Retourne une vue croisée de tous les Part Numbers sur tous les projets.

        Pour chaque Part Number unique (toutes bases confondues), retourne :
          - apqp          : Code APQP du record
          - part_name     : Nom du composant
          - part_number   : Numéro de pièce
          - project_count : Nombre de projets DISTINCTS dans lesquels ce PN apparaît.
                            Utilisé par la couche Python pour calculer New / CO :
                            project_count == 1  → "New"
                            project_count  > 1  → "CO" (Carry-Over)
          - proj_<id>     : True si le PN est présent dans le projet <id>

        Note : l'ancienne clé "is_new" (booléen) a été supprimée. La logique
        New / CO est désormais calculée dans compute_new_co() (pages/cross_project_view.py).

        Returns:
            Liste de dicts représentant les composants avec leur présence par projet.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # 1. Récupérer tous les projets existants
            cur.execute("SELECT id, code, name FROM projects ORDER BY code")
            all_projects = [dict(row) for row in cur.fetchall()]

            # 2. Récupérer TOUS les records (tous projets confondus)
            cur.execute("""
                SELECT
                    cr.project_id,
                    cr.part_number,
                    cr.part_name,
                    cr.apqp
                FROM cmf_records cr
                WHERE cr.part_number IS NOT NULL AND TRIM(cr.part_number) != ''
                ORDER BY cr.part_number
            """)
            rows = [dict(row) for row in cur.fetchall()]

            # 3. Construire l'index : part_number -> {project_ids: set, ...}
            pn_map: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                pn = row["part_number"].strip()
                if pn not in pn_map:
                    pn_map[pn] = {
                        "part_number": pn,
                        "part_name":   row["part_name"] or "",
                        "apqp":        row["apqp"] or "",
                        "project_ids": set(),
                    }
                # Compléter part_name / apqp si encore vides
                if not pn_map[pn]["part_name"] and row["part_name"]:
                    pn_map[pn]["part_name"] = row["part_name"]
                if not pn_map[pn]["apqp"] and row["apqp"]:
                    pn_map[pn]["apqp"] = row["apqp"]
                pn_map[pn]["project_ids"].add(row["project_id"])

            # 4. Construire la liste finale
            result = []
            for pn, info in pn_map.items():
                project_ids = info["project_ids"]
                entry: Dict[str, Any] = {
                    "apqp":          info["apqp"],
                    "part_name":     info["part_name"],
                    "part_number":   pn,
                    # Nombre de projets distincts → utilisé pour calculer New / CO
                    "project_count": len(project_ids),
                    # NB : "is_new" supprimé – utiliser project_count == 1 à la place
                }
                # Indicateur de présence par projet (True/False)
                for proj in all_projects:
                    entry[f"proj_{proj['id']}"] = proj["id"] in project_ids
                result.append(entry)

            return result

        finally:
            close_connection(conn)


    def get_all_projects_for_cross_view(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste de tous les projets (id, code, name) pour construire
        les en-têtes de la vue croisée.

        Returns:
            Liste de dicts {id, code, name}
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, code, name FROM projects ORDER BY code")
            return [dict(row) for row in cur.fetchall()]
        finally:
            close_connection(conn)

    def get_record_raw(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Retourne un record RAW (dictionnaire) avec TOUS les champs.
        
        Args:
            record_id: ID du record
            
        Returns:
            Dictionnaire avec tous les champs, ou None
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cmf_records WHERE id = ?", (record_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            close_connection(conn)
