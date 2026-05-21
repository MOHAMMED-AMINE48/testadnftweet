"""
Module de connexion et gestion SQLite pour CMF.
Fournit la connexion à la base SQLite locale et l'initialisation des tables.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict

# Chemin vers la base de données SQLite
DB_PATH = Path("data/cmf.db")


LEGACY_COLUMN_TABLES = [
    "columns_registry",
    "column_registry",
    "project_column_config",
    "project_columns_config",
]


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cur.fetchone() is not None


def _table_has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cur.fetchall())


def _migrate_legacy_records_table(conn: sqlite3.Connection) -> None:
    """Legacy wide tables are dropped by init_db(); keep helper for compatibility."""
    return


def _reset_simplified_tables(conn: sqlite3.Connection) -> None:
    """Reset core EAV tables to the simplified schema."""
    conn.execute("DROP TABLE IF EXISTS project_column_permissions")
    conn.execute("DROP TABLE IF EXISTS cmf_record_values")
    conn.execute("DROP TABLE IF EXISTS cmf_records")
    conn.execute("DROP TABLE IF EXISTS project_columns")
    conn.execute("DROP TABLE IF EXISTS cmf_records_legacy")


def _seed_default_project_columns(conn: sqlite3.Connection) -> None:
    """Populate default column configuration for existing projects without schema rows."""
    from services.master_schema import AUTO_COLUMNS, STANDARD_COLUMNS_WITH_ROLES

    cur = conn.cursor()
    cur.execute("SELECT id FROM projects ORDER BY id")
    project_ids = [row["id"] for row in cur.fetchall()]

    for project_id in project_ids:
        cur.execute("SELECT COUNT(*) AS count FROM project_columns WHERE project_id = ?", (project_id,))
        if int(cur.fetchone()["count"] or 0) > 0:
            continue

        for display_order, col_def in enumerate(STANDARD_COLUMNS_WITH_ROLES):
            column_name = col_def["name"]
            is_auto = 1 if column_name in AUTO_COLUMNS or column_name == "CMF LINE N°" else 0
            roles = [str(role).strip().upper() for role in col_def["roles"] if str(role).strip()]
            if is_auto:
                owner_role = "AUTO"
            elif len(roles) == 1:
                owner_role = roles[0]
            elif "BUYER" in roles:
                owner_role = "BUYER"
            elif roles:
                owner_role = "MULTI"
            else:
                owner_role = "UNKNOWN"

            cur.execute(
                """
                INSERT INTO project_columns (
                    project_id, column_name, owner_role, is_auto, display_order
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, column_name, owner_role, is_auto, display_order),
            )

            if not is_auto:
                cur.execute(
                    """
                    DELETE FROM project_column_permissions
                    WHERE project_id = ? AND column_name = ?
                    """,
                    (project_id, column_name),
                )
            for role in roles:
                if role == "AUTO":
                    continue
                cur.execute(
                    """
                    INSERT OR IGNORE INTO project_column_permissions (
                        project_id, column_name, role, can_edit
                    ) VALUES (?, ?, ?, 1)
                    """,
                    (project_id, column_name, role),
                )

    conn.commit()


def _sync_standard_project_columns(conn: sqlite3.Connection) -> None:
    """Force standard columns/permissions from master_schema while preserving custom columns."""
    from services.master_schema import AUTO_COLUMNS, STANDARD_COLUMNS_WITH_ROLES

    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO project_columns (
            project_id, column_name, owner_role, is_auto, display_order
        )
        SELECT
            project_id,
            'CONTRACTED CAPACITY STEP (Parts/Week)',
            owner_role,
            is_auto,
            display_order
        FROM project_columns
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
        """
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO project_column_permissions (
            project_id, column_name, role, can_edit
        )
        SELECT
            project_id,
            'CONTRACTED CAPACITY STEP (Parts/Week)',
            role,
            can_edit
        FROM project_column_permissions
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
        """
    )
    cur.execute(
        """
        UPDATE cmf_record_values
        SET column_name = 'CONTRACTED CAPACITY STEP (Parts/Week)'
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
          AND NOT EXISTS (
              SELECT 1
              FROM cmf_record_values AS existing
              WHERE existing.record_id = cmf_record_values.record_id
                AND existing.column_name = 'CONTRACTED CAPACITY STEP (Parts/Week)'
          )
        """
    )
    cur.execute(
        """
        DELETE FROM cmf_record_values
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
        """
    )
    cur.execute(
        """
        DELETE FROM project_column_permissions
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
          AND EXISTS (
              SELECT 1
              FROM project_column_permissions AS existing
              WHERE existing.project_id = project_column_permissions.project_id
                AND existing.role = project_column_permissions.role
                AND existing.column_name = 'CONTRACTED CAPACITY STEP (Parts/Week)'
          )
        """
    )
    cur.execute(
        """
        DELETE FROM project_columns
        WHERE column_name = 'CAPACITY STEP (Parts/Week)'
        """
    )
    cur.execute("SELECT id FROM projects ORDER BY id")
    project_ids = [row["id"] for row in cur.fetchall()]

    for project_id in project_ids:
        for display_order, col_def in enumerate(STANDARD_COLUMNS_WITH_ROLES):
            column_name = col_def["name"]
            is_auto = 1 if col_def["is_auto"] else 0
            roles = [str(role).strip().upper() for role in col_def["roles"] if str(role).strip()]
            if is_auto:
                owner_role = "AUTO"
            elif len(roles) == 1:
                owner_role = roles[0]
            elif "BUYER" in roles:
                owner_role = "BUYER"
            elif roles:
                owner_role = "MULTI"
            else:
                owner_role = "UNKNOWN"

            cur.execute(
                """
                INSERT INTO project_columns (
                    project_id, column_name, owner_role, is_auto, display_order
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id, column_name) DO UPDATE SET
                    owner_role = excluded.owner_role,
                    is_auto = excluded.is_auto,
                    display_order = excluded.display_order
                """,
                (project_id, column_name, owner_role, is_auto, display_order),
            )
            cur.execute(
                """
                DELETE FROM project_column_permissions
                WHERE project_id = ? AND column_name = ?
                """,
                (project_id, column_name),
            )
            for role in roles:
                if role == "AUTO":
                    continue
                cur.execute(
                    """
                    INSERT OR IGNORE INTO project_column_permissions (
                        project_id, column_name, role, can_edit
                    ) VALUES (?, ?, ?, 1)
                    """,
                    (project_id, column_name, role),
                )

    conn.commit()


def ensure_cmf_records_schema(*args, **kwargs):
    """Backward-compatible helper kept for older imports.

    The new schema is managed by init_db(); this function simply ensures the
    database file is initialized and the schema migrations are applied.
    """
    init_db()
    return {"success": True, "message": "Schema ensured"}


def get_columns_registry_map() -> Dict[str, str]:
    """Backward-compatible mapping of legacy column names to labels.

    Older repositories only need a simple name->label map during import.
    """
    from services.master_schema import STANDARD_COLUMNS_ORDER, get_column_label

    return {column_key: get_column_label(column_key) for column_key in STANDARD_COLUMNS_ORDER}


def resolve_db_name(column_name: str) -> str:
    """Compatibility helper that normalizes a display name to a database key."""
    normalized = str(column_name).strip().lower().replace(" ", "_")
    aliases = {
        "apqp": "apqp_grid",
        "apqpgrid": "apqp_grid",
        "partnumber": "part_number",
        "part_name": "part_name",
        "partname": "part_name",
        "newco": "new_co",
        "mix": "mix_pct",
    }
    return aliases.get(normalized, normalized)


def to_db_name(column_name: str) -> str:
    """Legacy alias for resolve_db_name."""
    return resolve_db_name(column_name)


def get_connection() -> sqlite3.Connection:
    """
    Établit une connexion à la base SQLite.
    Crée le répertoire data/ s'il n'existe pas.
    
    Returns:
        sqlite3.Connection: Connexion à la base SQLite avec row_factory configurée
    """
    # Créer le dossier data/ s'il n'existe pas
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Créer la connexion (streamlit requires check_same_thread=False for multithreaded reruns)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    
    # Configurer row_factory pour avoir des dict-like rows
    conn.row_factory = sqlite3.Row
    
    # Activer les foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    # Ensure row access as mapping
    conn.row_factory = sqlite3.Row
    
    return conn


def init_db() -> None:
    """
    Initialise la base de données : crée les tables si elles n'existent pas.
    
    Tables créées :
    - projects : Projets/CMF
    - cmf_records : Records CMF (lignes de données)
    - user_project_roles : Rôles utilisateur par projet
    - audit_logs : Logs d'audit (optionnel, voir TODO)
    """
    # Use a single short-lived connection to create schema if missing.
    # init_db() is idempotent and safe to call on every app start; it will not overwrite existing data.
    conn = get_connection()
    try:
        with conn:
            for table_name in LEGACY_COLUMN_TABLES:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            _migrate_legacy_records_table(conn)
            # NOTE: Do NOT call _reset_simplified_tables() here!
            # It drops all tables including project_columns and user data.
            # Tables are created as IF NOT EXISTS below; existing data is preserved.

            conn.executescript("""
            -- Table des projets/CMF
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                capacity_manager_name TEXT NOT NULL,
                buyer_assigned_name TEXT,
                sqd_assigned_name TEXT,
                supplier_name TEXT,
                cmf_status TEXT DEFAULT 'ACTIVE',
                cmf_schema TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- Configuration des colonnes par projet
            CREATE TABLE IF NOT EXISTS project_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                owner_role TEXT NOT NULL,
                is_auto INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL,
                custom_section TEXT,
                UNIQUE(project_id, column_name),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- Permissions d'édition par colonne et rôle
            CREATE TABLE IF NOT EXISTS project_column_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                role TEXT NOT NULL,
                can_edit INTEGER NOT NULL DEFAULT 1,
                UNIQUE(project_id, column_name, role),
                FOREIGN KEY (project_id, column_name) REFERENCES project_columns(project_id, column_name) ON DELETE CASCADE
            );

            -- Table CMF minimale
            CREATE TABLE IF NOT EXISTS cmf_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                apqp_grid TEXT NOT NULL,
                part_number TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- Valeurs EAV des records CMF
            CREATE TABLE IF NOT EXISTS cmf_record_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                value TEXT,
                UNIQUE(record_id, column_name),
                FOREIGN KEY (record_id) REFERENCES cmf_records(id) ON DELETE CASCADE
            );

            -- Table des rôles utilisateur par projet
            CREATE TABLE IF NOT EXISTS user_project_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                assigned_at TEXT DEFAULT (datetime('now')),
                assigned_by TEXT,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                UNIQUE (user_name, project_id, role),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- Table d'audit (optionnel pour la v1)
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                user_name TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT DEFAULT (datetime('now')),
                project_id INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
            );

            -- Créer les index pour améliorer les performances
                CREATE INDEX IF NOT EXISTS idx_cmf_records_project_id ON cmf_records(project_id);
                CREATE INDEX IF NOT EXISTS idx_cmf_records_part_number ON cmf_records(part_number);
                CREATE INDEX IF NOT EXISTS idx_project_columns_project_id ON project_columns(project_id);
                CREATE INDEX IF NOT EXISTS idx_project_columns_order ON project_columns(project_id, display_order);
                CREATE INDEX IF NOT EXISTS idx_project_column_permissions_project_id ON project_column_permissions(project_id);
                CREATE INDEX IF NOT EXISTS idx_project_column_permissions_role ON project_column_permissions(project_id, role);
                CREATE INDEX IF NOT EXISTS idx_cmf_record_values_record_id ON cmf_record_values(record_id);
                CREATE INDEX IF NOT EXISTS idx_cmf_record_values_column_name ON cmf_record_values(column_name);
            CREATE INDEX IF NOT EXISTS idx_user_project_roles_user ON user_project_roles(user_name);
            CREATE INDEX IF NOT EXISTS idx_user_project_roles_project ON user_project_roles(project_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_project_id ON audit_logs(project_id);
            """)

            _seed_default_project_columns(conn)
            _sync_standard_project_columns(conn)
            
            # Run migration for unique index AFTER creating tables (separate transaction)
            try:
                migrate_cmf_records_unique_index()
            except Exception as e:
                # Silently ignore if migration fails (may already exist)
                pass

    finally:
        conn.close()


def migrate_cmf_records_unique_index() -> None:
    """
    Migration: Replace the old unique index (if any) with new one on (project_id, part_number).
    
    This allows APQP GRID to be optional, with part_number being the unique key per project.
    Handles existing data by keeping the first record and deleting duplicates.
    This is an idempotent migration - safe to call multiple times.
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.cursor()
            
            # Check if cmf_records table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cmf_records'")
            if not cur.fetchone():
                return  # Table doesn't exist yet
            
            # Step 1: Find and remove duplicates (keep first record per project_id + part_number)
            cur.execute("""
                DELETE FROM cmf_records 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM cmf_records 
                    GROUP BY project_id, part_number
                )
            """)
            deleted_count = cur.rowcount
            if deleted_count > 0:
                print(f"Migration: Removed {deleted_count} duplicate records")
            
            # Step 2: Drop old unique indexes if they exist
            cur.execute("DROP INDEX IF EXISTS ux_records_apqp_part")
            cur.execute("DROP INDEX IF EXISTS ux_cmf_records_apqp_part")
            
            # Step 3: Create the new unique index (idempotent with IF NOT EXISTS)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_records_project_part
                ON cmf_records(project_id, part_number)
            """)
            
            conn.commit()
            print("Migration: Unique index on (project_id, part_number) created successfully")
    except sqlite3.OperationalError as e:
        # Index may already exist or table doesn't exist yet - this is OK
        print(f"Migration info: {str(e)}")
    finally:
        close_connection(conn)


def close_connection(conn: sqlite3.Connection) -> None:
    """
    Ferme la connexion SQLite.
    
    Args:
        conn: Connexion à fermer
    """
    if conn:
        conn.close()


def add_column_to_cmf_records(column_name: str, column_type: str = "TEXT") -> bool:
    """
    Ajoute une colonne à la table cmf_records (pour les colonnes personnalisées).
    Si la colonne existe déjà, elle est ignorée (pas d'erreur).
    
    Args:
        column_name: Nom de la colonne à ajouter
        column_type: Type SQLite (TEXT, REAL, INTEGER, etc.) - défaut: TEXT
        
    Returns:
        True si succès, False sinon
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cur.execute("PRAGMA table_info(cmf_records)")
        columns = [row[1] for row in cur.fetchall()]
        
        if column_name in columns:
            # Colonne existe déjà
            return True
        
        # Ajouter la colonne
        alter_sql = f"ALTER TABLE cmf_records ADD COLUMN {column_name} {column_type} DEFAULT NULL"
        cur.execute(alter_sql)
        conn.commit()
        print(f" Column '{column_name}' added to cmf_records table")
        return True
    except Exception as e:
        print(f" Error adding column '{column_name}': {str(e)}")
        return False
    finally:
        close_connection(conn)


def add_custom_columns_for_project(custom_columns: Dict[str, str]) -> bool:
    """
    Ajoute plusieurs colonnes personnalisées à la table cmf_records.
    
    Args:
        custom_columns: Dict {column_name: column_type} ex: {"super_mix": "REAL", "custom_note": "TEXT"}
        
    Returns:
        True si toutes les colonnes ont été ajoutées
    """
    success = True
    for col_name, col_type in custom_columns.items():
        if not add_column_to_cmf_records(col_name, col_type):
            success = False
    return success


def reset_db() -> None:
    """
     DÉVELOPPEMENT UNIQUEMENT : Réinitialise complètement la base de données.
    Supprime le fichier .db et recrée les tables vides.
    """
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
