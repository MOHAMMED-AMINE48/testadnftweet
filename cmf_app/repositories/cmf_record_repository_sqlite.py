"""SQLite repository for CMF records using an EAV storage model."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from db_sqlite import close_connection, get_connection
from repositories.project_column_repository_sqlite import ProjectColumnRepository
from services.calculations import compute_cat_valuation
from services.master_schema import AUTO_COLUMNS

APQP_KEY = "APQP GRID"
PART_NUMBER_KEY = "PART NUMBER"
WEEKLY_CAPACITY_CONTRACTED = "WEEKLY CAPACITY CONTRACTED (Parts/Week)"
LAST_WEEKLY_CAPACITY_REQUESTED = "LAST WEEKLY CAPACITY REQUESTED"
WEEKLY_CAPACITY_TO_MEASURE = "WEEKLY CAPACITY TO MEASURE"
YEAR_OF_MAX_NEED = "YEAR OF MAX NEED"
CAPACITY_SOURCE = "CAPACITY SOURCE"
GOR_KEY = "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer"
WEEKLY_CAPACITY_MEASURED = "WEEKLY CAPACITY MEASURED"
WEEKLY_CAPACITY_ESTIMATED = "WEEKLY CAPACITY ESTIMATED"
CAT_VALUATION_KEY = "CAT1/2/3 VALUATION (G;O;R)"


@dataclass
class CMFRecord:
    id: int
    project_id: int
    apqp_grid: str
    part_number: str
    status: str = "PRESOURCING"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    values: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, item: str):
        aliases = {
            "apqp": "apqp_grid",
            "partname": "fac_rfq_pd_letter",
        }
        key = aliases.get(item, item)
        if key in self.__dict__:
            return self.__dict__[key]
        if key in self.values:
            return self.values[key]
        return ""

    def __setattr__(self, key: str, value: Any) -> None:
        if key in {"id", "project_id", "apqp_grid", "part_number", "status", "created_at", "updated_at", "updated_by", "values"}:
            object.__setattr__(self, key, value)
        else:
            self.values[key] = value

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "apqp_grid": self.apqp_grid,
            "part_number": self.part_number,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }
        data.update(self.values)
        data["apqp"] = self.apqp_grid
        return data


class CMFRecordRepository:
    """Repository implementing the new EAV model."""

    @staticmethod
    def _canonical_input_key(key: str) -> str:
        value = str(key).strip()
        aliases = {
            "apqp": "apqp_grid",
            "apqp_grid": "apqp_grid",
            APQP_KEY: "apqp_grid",
            "part_number": "part_number",
            "part number": "part_number",
            PART_NUMBER_KEY: "part_number",
        }
        return aliases.get(value, value)

    def _normalize_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in data.items():
            normalized[self._canonical_input_key(key)] = value
        return normalized

    def __init__(self) -> None:
        self.project_column_repo = ProjectColumnRepository()

    def _load_record_values(self, record_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not record_ids:
            return {}

        conn = get_connection()
        try:
            placeholders = ",".join(["?"] * len(record_ids))
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT record_id, column_name, value
                FROM cmf_record_values
                WHERE record_id IN ({placeholders})
                """,
                record_ids,
            )
            values_by_record: Dict[int, Dict[str, Any]] = {record_id: {} for record_id in record_ids}
            for row in cur.fetchall():
                values_by_record[row["record_id"]][row["column_name"]] = row["value"]
            return values_by_record
        finally:
            close_connection(conn)

    def _load_project_column_labels(self, project_id: int) -> Dict[str, str]:
        columns = self.project_column_repo.get_project_columns(project_id)
        return {column.column_name: column.column_name for column in columns}

    def _compute_auto_values(self, data: Dict[str, Any], record_id: Optional[int] = None) -> Dict[str, Any]:
        auto_values: Dict[str, Any] = {}
        if "CMF LINE N°" in AUTO_COLUMNS:
            auto_values["CMF LINE N°"] = record_id or data.get("id") or ""

        if WEEKLY_CAPACITY_TO_MEASURE in AUTO_COLUMNS:
            auto_values[WEEKLY_CAPACITY_TO_MEASURE] = data.get(WEEKLY_CAPACITY_CONTRACTED) or data.get(WEEKLY_CAPACITY_TO_MEASURE) or ""

        if YEAR_OF_MAX_NEED in AUTO_COLUMNS:
            auto_values[YEAR_OF_MAX_NEED] = data.get(CAPACITY_SOURCE) or data.get(YEAR_OF_MAX_NEED) or ""

        contracted = self._to_float(data.get(WEEKLY_CAPACITY_CONTRACTED))
        requested = self._to_float(data.get(LAST_WEEKLY_CAPACITY_REQUESTED))
        if contracted is not None and requested is not None and requested > 0:
            ratio = contracted / requested
            if ratio >= 1:
                gor = "G"
            elif ratio >= 0.8:
                gor = "O"
            else:
                gor = "R"
            auto_values[GOR_KEY] = gor

        auto_values[CAT_VALUATION_KEY] = compute_cat_valuation(
            {
                WEEKLY_CAPACITY_CONTRACTED: data.get(WEEKLY_CAPACITY_CONTRACTED),
                LAST_WEEKLY_CAPACITY_REQUESTED: data.get(LAST_WEEKLY_CAPACITY_REQUESTED),
                WEEKLY_CAPACITY_MEASURED: data.get(WEEKLY_CAPACITY_MEASURED),
            }
        )

        return auto_values

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def get_record_by_composite_key(self, project_id: int, apqp_grid: str, part_number: str) -> Optional[CMFRecord]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM cmf_records
                WHERE project_id = ? AND apqp_grid = ? AND part_number = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_id, str(apqp_grid).strip(), str(part_number).strip()),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self.get_record_by_id(int(row["id"]))
        finally:
            close_connection(conn)

    def ensure_record(self, project_id: int, part_number: str, values: Optional[Dict[str, Any]] = None, updated_by: str = "system", apqp: Optional[str] = None) -> int:
        """
        Ensures a record exists for the given part_number. 
        If apqp is not provided but exists in values, use it for lookup.
        
        Args:
            project_id: Project ID
            part_number: Part number (required)
            values: Optional dict of values to set/update
            updated_by: User making the update
            apqp: Optional APQP GRID value
            
        Returns:
            Record ID
        """
        # Try to find existing record by part_number + apqp (if apqp is provided)
        if not apqp and values:
            apqp = str(values.get("apqp_grid") or values.get("apqp") or "").strip()
        
        apqp_to_use = str(apqp or "").strip()
        part_to_use = str(part_number or "").strip()
        
        # Try to find by both keys if apqp is provided
        if apqp_to_use and part_to_use:
            existing = self.get_record_by_composite_key(project_id, apqp_to_use, part_to_use)
            if existing:
                # Update if values provided
                if values:
                    self.update_record(existing.id, values, updated_by)
                return existing.id
        
        # Try to find by part_number only (new behavior)
        if part_to_use:
            existing_by_pn = self.find_record_by_part_number(project_id, part_to_use)
            if existing_by_pn:
                if values:
                    self.update_record(existing_by_pn, values, updated_by)
                return existing_by_pn
        
        # Create new record
        record_data = {"part_number": part_to_use}
        if apqp_to_use:
            record_data["apqp_grid"] = apqp_to_use
        if values:
            record_data.update(values)
        
        record = self.create_record(
            project_id=project_id,
            data=record_data,
            updated_by=updated_by,
        )
        return record.id

    def find_or_none(self, project_id: int, apqp: str, part_number: str) -> Optional[int]:
        record = self.get_record_by_composite_key(project_id, apqp, part_number)
        return record.id if record else None

    def find_record_by_part_number(self, project_id: int, part_number: str) -> Optional[int]:
        """Find a record by part number only (not using APQP grid)."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id
                FROM cmf_records
                WHERE project_id = ? AND part_number = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_id, str(part_number).strip()),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
        finally:
            close_connection(conn)

    def exists(self, project_id: int, part_number: str) -> bool:
        """Check if a record with the given part number exists in the project."""
        record_id = self.find_record_by_part_number(project_id, part_number)
        return record_id is not None

    def get_values_for_record(self, record_id: int, column_names: List[str]) -> Dict[str, Any]:
        record = self.get_record_by_id(record_id)
        if not record:
            return {column_name: None for column_name in column_names}

        record_dict = record.to_dict()
        values: Dict[str, Any] = {}
        for column_name in column_names:
            normalized = str(column_name).strip()
            if normalized in {"APQP GRID", "apqp_grid"}:
                values[column_name] = record_dict.get("apqp_grid", "")
            elif normalized in {"PART NUMBER", "part_number"}:
                values[column_name] = record_dict.get("part_number", "")
            else:
                values[column_name] = record_dict.get(normalized, record.values.get(normalized))
        return values

    def _recalculate_cat_valuation(self, record_id: int) -> str:
        values = self.get_values_for_record(
            record_id,
            [
                WEEKLY_CAPACITY_CONTRACTED,
                LAST_WEEKLY_CAPACITY_REQUESTED,
                WEEKLY_CAPACITY_MEASURED,
            ],
        )
        valuation = compute_cat_valuation(values)
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO cmf_record_values (record_id, column_name, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
                    """,
                    (record_id, CAT_VALUATION_KEY, valuation),
                )
        finally:
            close_connection(conn)
        return valuation

    def upsert_value(self, record_id: int, column_name: str, value: Any, updated_by: Optional[str] = None) -> None:
        del updated_by
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO cmf_record_values (record_id, column_name, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
                    """,
                    (record_id, str(column_name).strip(), None if value is None else str(value)),
                )
        finally:
            close_connection(conn)

        self._recalculate_cat_valuation(record_id)

    def update_values(self, record_id: int, updates: Dict[str, Any], updated_by: Optional[str] = None) -> None:
        del updated_by
        normalized_updates = {
            key: value
            for key, value in self._normalize_payload(updates).items()
            if key not in {"id", "project_id"} and key not in AUTO_COLUMNS
        }
        if not normalized_updates:
            return

        conn = get_connection()
        try:
            with conn:
                for column_name, value in normalized_updates.items():
                    conn.execute(
                        """
                        INSERT INTO cmf_record_values (record_id, column_name, value)
                        VALUES (?, ?, ?)
                        ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
                        """,
                        (record_id, str(column_name).strip(), None if value is None else str(value)),
                    )
        finally:
            close_connection(conn)

        self._recalculate_cat_valuation(record_id)

    def create_record(self, project_id: int, data: Dict[str, Any], updated_by: str, status: str = "PRESOURCING") -> CMFRecord:
        data = self._normalize_payload({key: value for key, value in data.items() if key not in {"id", "project_id"}})
        apqp_grid = str(data.get("apqp_grid") or data.get("apqp") or "").strip()
        part_number = str(data.get("part_number") or "").strip()
        # PART NUMBER is now the only required field; APQP can be empty
        if not part_number:
            raise ValueError("Required field missing: part_number")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO cmf_records (
                    project_id, apqp_grid, part_number
                ) VALUES (?, ?, ?)
                """,
                (project_id, apqp_grid, part_number),
            )
            record_id = cur.lastrowid

            auto_values = self._compute_auto_values(data, record_id=record_id)
            stored_values = {**data, **auto_values}
            columns = self.project_column_repo.get_project_columns(project_id)
            allowed_columns = {column.column_name for column in columns if column.column_name not in {"apqp_grid", "part_number", "APQP GRID", "PART NUMBER"}}
            allowed_columns.update(auto_values.keys())

            rows_to_insert = []
            for column_name, value in stored_values.items():
                if column_name in {"apqp_grid", "part_number", "status", "created_at", "updated_at", "updated_by"}:
                    continue
                if column_name not in allowed_columns and column_name not in AUTO_COLUMNS:
                    continue
                rows_to_insert.append((record_id, column_name, None if value is None else str(value)))

            if rows_to_insert:
                cur.executemany(
                    """
                    INSERT INTO cmf_record_values (record_id, column_name, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
                    """,
                    rows_to_insert,
                )

            conn.commit()
            self._recalculate_cat_valuation(record_id)
            return self.get_record_by_id(record_id)
        finally:
            close_connection(conn)

    def update_record(self, record_id: int, data: Dict[str, Any], updated_by: str) -> Optional[CMFRecord]:
        existing = self.get_record_by_id(record_id)
        if not existing:
            return None

        data = self._normalize_payload(data)
        conn = get_connection()
        try:
            cur = conn.cursor()
            apqp_grid = str(data.get("apqp_grid") or data.get("apqp") or existing.apqp_grid or "").strip()
            part_number = str(data.get("part_number") or existing.part_number or "").strip()
            # PART NUMBER is now the only required field
            if not part_number:
                raise ValueError("Required field missing: part_number")

            cur.execute(
                """
                UPDATE cmf_records
                SET apqp_grid = ?, part_number = ?
                WHERE id = ?
                """,
                (apqp_grid, part_number, record_id),
            )

            cleanup_keys = {"id", "project_id", "apqp_grid", "apqp", "part_number", "status", "created_at", "updated_at", "updated_by"}
            auto_values = self._compute_auto_values(data, record_id=record_id)
            values_payload = {**data, **auto_values}
            rows_to_upsert = []
            for column_name, value in values_payload.items():
                if column_name in cleanup_keys:
                    continue
                rows_to_upsert.append((record_id, column_name, None if value is None else str(value)))

            if rows_to_upsert:
                cur.executemany(
                    """
                    INSERT INTO cmf_record_values (record_id, column_name, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
                    """,
                    rows_to_upsert,
                )

            conn.commit()
            self._recalculate_cat_valuation(record_id)
            return self.get_record_by_id(record_id)
        finally:
            close_connection(conn)

    def delete_record(self, record_id: int) -> bool:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM cmf_records WHERE id = ?", (record_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            close_connection(conn)

    def get_record_by_id(self, record_id: int) -> Optional[CMFRecord]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cmf_records WHERE id = ?", (record_id,))
            record_row = cur.fetchone()
            if not record_row:
                return None
            values_by_record = self._load_record_values([record_id]).get(record_id, {})
            return self._row_to_record(record_row, values_by_record)
        finally:
            close_connection(conn)

    def get_records_for_project(self, project_id: int, status: Optional[str] = None) -> List[CMFRecord]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cmf_records WHERE project_id = ? ORDER BY id", (project_id,))
            rows = cur.fetchall()
            record_ids = [row["id"] for row in rows]
            values_by_record = self._load_record_values(record_ids)
            return [self._row_to_record(row, values_by_record.get(row["id"], {})) for row in rows]
        finally:
            close_connection(conn)

    def get_records_raw(self, project_id: int) -> List[Dict[str, Any]]:
        return [record.to_dict() for record in self.get_records_for_project(project_id)]

    def count_records_for_project(self, project_id: int) -> int:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM cmf_records WHERE project_id = ?", (project_id,))
            row = cur.fetchone()
            return int(row["count"] if row else 0)
        finally:
            close_connection(conn)

    def get_cross_project_part_number_view(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    cr.apqp_grid AS apqp,
                    cr.part_number,
                    cr.project_id,
                    p.code AS project_code,
                    p.name AS project_name
                FROM cmf_records cr
                JOIN projects p ON p.id = cr.project_id
                ORDER BY cr.part_number, cr.project_id
                """
            )
            rows = cur.fetchall()
            by_part_number: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                part_number = (row["part_number"] or "").strip()
                if not part_number:
                    continue
                entry = by_part_number.setdefault(
                    part_number,
                    {"apqp": row["apqp"], "part_number": part_number, "part_name": ""},
                )
                entry[f"proj_{row['project_id']}"] = True
            return list(by_part_number.values())
        finally:
            close_connection(conn)

    def get_all_projects_for_cross_view(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, code, name FROM projects ORDER BY code")
            return [dict(row) for row in cur.fetchall()]
        finally:
            close_connection(conn)

    def _row_to_record(self, row, values: Dict[str, Any]) -> CMFRecord:
        record = CMFRecord(
            id=row["id"],
            project_id=row["project_id"],
            apqp_grid=row["apqp_grid"],
            part_number=row["part_number"],
            status=row["status"] if "status" in row.keys() else "ACTIVE",
            created_at=row["created_at"] if "created_at" in row.keys() else None,
            updated_at=row["last_updated"] if "last_updated" in row.keys() else (row["updated_at"] if "updated_at" in row.keys() else None),
            updated_by=row["updated_by"] if "updated_by" in row.keys() else None,
            values={},
        )
        for key, value in values.items():
            if key in {"apqp_grid", "part_number"}:
                continue
            record.values[key] = value
        auto_values = self._compute_auto_values(record.to_dict(), record_id=record.id)
        record.values.update(auto_values)
        return record

    def exists(self, project_id: int, part_number: str) -> bool:
        """Check if a Part Number exists in a project."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as count FROM cmf_records WHERE project_id = ? AND part_number = ?",
                (project_id, str(part_number).strip())
            )
            row = cur.fetchone()
            return int(row["count"] if row else 0) > 0
        finally:
            close_connection(conn)

    def get_part_numbers(self, project_id: int) -> List[str]:
        """Get all unique Part Numbers for a project, sorted."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT part_number FROM cmf_records WHERE project_id = ? AND part_number IS NOT NULL AND part_number != '' ORDER BY part_number",
                (project_id,)
            )
            rows = cur.fetchall()
            return [str(row["part_number"]).strip() for row in rows]
        finally:
            close_connection(conn)

    def ensure_composite_index(self) -> None:
        """Ensure the composite unique index exists on cmf_record_values."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_cmf_record_values_record_column
                ON cmf_record_values (record_id, column_name)
            """)
            conn.commit()
        finally:
            close_connection(conn)

    def ensure_column_for_project(self, project_id: int, column_name: str, owner_role: str = "BUYER") -> None:
        """Ensure a column is registered in project_columns for a project."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Check if already exists
            cur.execute("""
                SELECT id FROM project_columns
                WHERE project_id = ? AND column_name = ?
            """, (project_id, column_name))
            
            if cur.fetchone() is None:
                # Insert new column
                cur.execute("""
                    INSERT INTO project_columns (project_id, column_name, owner_role, is_auto, display_order)
                    VALUES (?, ?, ?, 0, 999)
                """, (project_id, column_name, owner_role))
            
            conn.commit()
        finally:
            close_connection(conn)

    def ensure_column_permissions(self, project_id: int, column_name: str, role: str = "BUYER", can_edit: bool = True) -> None:
        """Ensure permissions are set for a column in a project."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Check if already exists
            cur.execute("""
                SELECT id FROM project_column_permissions
                WHERE project_id = ? AND column_name = ? AND role = ?
            """, (project_id, column_name, role))
            
            if cur.fetchone() is None:
                # Insert new permission
                cur.execute("""
                    INSERT INTO project_column_permissions (project_id, column_name, role, can_edit)
                    VALUES (?, ?, ?, ?)
                """, (project_id, column_name, role, 1 if can_edit else 0))
            
            conn.commit()
        finally:
            close_connection(conn)

    def get_record_id_by_part_number(self, project_id: int, part_number: str) -> Optional[int]:
        """Get record_id by project_id and part_number."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM cmf_records
                WHERE project_id = ? AND part_number = ?
                LIMIT 1
            """, (project_id, str(part_number).strip()))
            
            row = cur.fetchone()
            return row["id"] if row else None
        finally:
            close_connection(conn)

    def update_capacity_by_part_number(self, project_id: int, part_number: str, capacity_value: float, updated_by: str) -> None:
        """Update WEEKLY CAPACITY CONTRACTED (Parts/Week) for a part identified by project_id and part_number."""
        
        # Ensure column and permissions exist
        self.ensure_composite_index()
        self.ensure_column_for_project(project_id, WEEKLY_CAPACITY_CONTRACTED, owner_role="BUYER")
        self.ensure_column_permissions(project_id, WEEKLY_CAPACITY_CONTRACTED, role="BUYER", can_edit=True)
        
        # Get record_id
        record_id = self.get_record_id_by_part_number(project_id, part_number)
        if record_id is None:
            raise ValueError(f"Part number '{part_number}' not found in project {project_id}")
        
        # Update capacity
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Upsert the capacity value
            cur.execute("""
                INSERT INTO cmf_record_values (record_id, column_name, value)
                VALUES (?, ?, ?)
                ON CONFLICT(record_id, column_name) DO UPDATE SET value = excluded.value
            """, (record_id, WEEKLY_CAPACITY_CONTRACTED, str(capacity_value)))
            
            conn.commit()
        finally:
            close_connection(conn)
        
        # Recalculate auto-values (GOR, CAT)
        self._recalculate_cat_valuation(record_id)


CMFRepository = CMFRecordRepository
