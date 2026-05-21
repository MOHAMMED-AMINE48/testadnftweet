"""Official CMF master schema definitions.

The standard CMF columns and role ownership are intentionally centralized here.
Project creation seeds SQLite from this list; standard permissions should not be
chosen manually in the UI.
"""

from typing import Dict, List, Optional, Set, TypedDict


class ColumnDef(TypedDict):
    name: str
    section: str
    roles: List[str]
    is_auto: bool


def _roles(*roles: str) -> List[str]:
    return [role.strip().upper() for role in roles if role and role.strip()]


STANDARD_COLUMNS_WITH_ROLES: List[ColumnDef] = [
    # PART DATA (STEP 1)
    {"name": "CMF LINE N°", "section": "PART DATA", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "N° SOURCING, RFQ,ODM,FETE …", "section": "PART DATA", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "APQP GRID", "section": "PART DATA", "roles": _roles("SQD"), "is_auto": False},
    {"name": "N° FAC / RFQ /PD LETTER", "section": "PART DATA", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "USE CASES", "section": "PART DATA", "roles": _roles("SQD"), "is_auto": False},
    {"name": "PART NUMBER", "section": "PART DATA", "roles": _roles("BUYER", "SQD"), "is_auto": False},
    {"name": "PART NAME", "section": "PART DATA", "roles": _roles("BUYER"), "is_auto": False},
    {
        "name": "PROCESS PART COEFFICIENT (precise definition: link between capacity and parts / vehicle production program)",
        "section": "PART DATA",
        "roles": _roles("BUYER", "SQD"),
        "is_auto": False,
    },

    # VEHICULES ROAD MAP (STEP 1) - Cross-Project View
    {"name": "ROADMAP", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 1", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 2", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 3", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 4", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 5", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 6", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 7", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 8", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 9", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 10", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "Project Code - Project Name 11", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "CarryOver - Adapted", "section": "VEHICULES ROAD MAP", "roles": _roles("AUTO"), "is_auto": True},

    # SUPPLIER INFORMATION (STEP 1)
    {"name": "SUPPLIER NAME", "section": "SUPPLIER INFORMATION", "roles": _roles("SQD"), "is_auto": False},
    {"name": "COUNTRY", "section": "SUPPLIER INFORMATION", "roles": _roles("SQD"), "is_auto": False},
    {"name": "LOCATION", "section": "SUPPLIER INFORMATION", "roles": _roles("SQD"), "is_auto": False},
    {"name": "COFOR", "section": "SUPPLIER INFORMATION", "roles": _roles("SQD"), "is_auto": False},
    {"name": "SQE", "section": "SUPPLIER INFORMATION", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "PROGRAM BUYER / BUYER", "section": "SUPPLIER INFORMATION", "roles": _roles("SQD"), "is_auto": False},

    # WEEKLY CONTRACTED CAPACITY (STEP 1 - STEP 3)
    {"name": "WEEKLY CAPACITY CONTRACTED (Parts/Week)", "section": "WEEKLY CONTRACTED CAPACITY", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "CONTRACTED CAPACITY STEP (Parts/Week)", "section": "WEEKLY CONTRACTED CAPACITY", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "LEAD TIME to implement Capacity Step (WEEKS)", "section": "WEEKLY CONTRACTED CAPACITY", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "INVESTMENT impact of Capacity Step (EURO)", "section": "WEEKLY CONTRACTED CAPACITY", "roles": _roles("BUYER"), "is_auto": False},
    {"name": "YEAR OF MAX NEED", "section": "WEEKLY CONTRACTED CAPACITY", "roles": _roles("AUTO"), "is_auto": True},
    {
        "name": "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer",
        "section": "WEEKLY CONTRACTED CAPACITY",
        "roles": _roles("AUTO"),
        "is_auto": True,
    },

    # CAPACITY SIZING (STEP 2)
    {"name": "SCR - SHARED FOLDER", "section": "CAPACITY SIZING", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "SCR DATE (DD/MM/YYYY)", "section": "CAPACITY SIZING", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "MIX (%)", "section": "CAPACITY SIZING", "roles": _roles("BUYER", "CAPACITY_MANAGER"), "is_auto": False},
    {"name": "LAST WEEKLY CAPACITY REQUESTED", "section": "CAPACITY SIZING", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "CAPACITY STEP (parts/week)", "section": "CAPACITY SIZING", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "CAPACITY SOURCE", "section": "CAPACITY SIZING", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},

    # CAPACITY WORKSHOP (STEP 2)
    {"name": "SUPERMIX ACTIVITY OUI/NON", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "SUPERMIX ACTIVITY Weekly Capacity", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "SUPERMIX ACTIVITY Commentaires", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "TKO DATE", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("SQD"), "is_auto": False},
    {"name": "USE KEY STATUS AFTER CAPACITY WORKSHOP (Effective Date)", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "CAPACITY WORKSHOP Done date", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "GT CAPACITY COLOR", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("CAPACITY_MANAGER"), "is_auto": False},
    {"name": "APQP Grid Project (Project Wave x)", "section": "CAPACITY WORKSHOP (STEP 2)", "roles": _roles("SQD"), "is_auto": False},

    # CAT (STEP 4)
    {"name": "WEEKLY CAPACITY TO MEASURE", "section": "CAT", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "CAT1 FORECASTED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT2 FORECASTED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT3 FORECASTED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT1/2/3 TYPE", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT1 REALISED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT2 REALISED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT3 REALISED DATE (YYCWxx)", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "WEEKLY CAPACITY MEASURED", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "WEEKLY CAPACITY ESTIMATED", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "CAT1/2/3 VALUATION (G;O;R)", "section": "CAT", "roles": _roles("AUTO"), "is_auto": True},
    {"name": "SHARED FOLDER - link", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
    {"name": "Comments", "section": "CAT", "roles": _roles("SQD"), "is_auto": False},
]


def get_standard_columns() -> List[str]:
    return [col["name"] for col in STANDARD_COLUMNS_WITH_ROLES]


def get_column_roles(column_name: str) -> List[str]:
    normalized = str(column_name).strip()
    for col in STANDARD_COLUMNS_WITH_ROLES:
        if col["name"] == normalized:
            return list(col["roles"])
    return []


def get_column_section(column_name: str) -> str:
    normalized = str(column_name).strip()
    for col in STANDARD_COLUMNS_WITH_ROLES:
        if col["name"] == normalized:
            return col["section"]
    return "CUSTOMIZED COLUMNS"


STANDARD_COLUMNS_ORDER = get_standard_columns()
AUTO_COLUMNS = {col["name"] for col in STANDARD_COLUMNS_WITH_ROLES if col["is_auto"]}
FIXED_COLUMNS = {"APQP GRID", "PART NUMBER"}

DEFAULT_VIEW_COLS = [
    "N° SOURCING, RFQ,ODM,FETE …",
    "APQP GRID",
    "USE CASES",
    "PART NUMBER",
    "WEEKLY CAPACITY CONTRACTED (Parts/Week)",
    "LAST WEEKLY CAPACITY REQUESTED",
    "WEEKLY CAPACITY MEASURED",
    "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer",
    "CAT1/2/3 VALUATION (G;O;R)",
]

STANDARD_COLUMNS_BY_ROLE = {
    "BUYER": [col["name"] for col in STANDARD_COLUMNS_WITH_ROLES if "BUYER" in col["roles"]],
    "CAPACITY_MANAGER": [col["name"] for col in STANDARD_COLUMNS_WITH_ROLES if "CAPACITY_MANAGER" in col["roles"]],
    "SQD": [col["name"] for col in STANDARD_COLUMNS_WITH_ROLES if "SQD" in col["roles"]],
    "AUTO": [col["name"] for col in STANDARD_COLUMNS_WITH_ROLES if col["is_auto"]],
}


def _primary_owner(col_def: ColumnDef) -> str:
    if col_def["is_auto"]:
        return "AUTO"
    roles = [role for role in col_def["roles"] if role != "AUTO"]
    if not roles:
        return "UNKNOWN"
    if len(roles) == 1:
        return roles[0]
    if "BUYER" in roles:
        return "BUYER"
    return "MULTI"


COLUMN_OWNER: Dict[str, str] = {col["name"]: _primary_owner(col) for col in STANDARD_COLUMNS_WITH_ROLES}

STANDARD_COLUMNS_BY_KEY = {
    col["name"]: {
        "key": col["name"],
        "label": col["name"],
        "section": col["section"],
        "roles": list(col["roles"]),
        "owner_role": COLUMN_OWNER[col["name"]],
        "is_auto": int(col["is_auto"]),
        "required": int(col["name"] in FIXED_COLUMNS),
    }
    for col in STANDARD_COLUMNS_WITH_ROLES
}

# Backward-compatible aliases
MASTER_COLUMNS_ORDER = STANDARD_COLUMNS_ORDER
COLUMN_TYPE = {column: "TEXT" for column in STANDARD_COLUMNS_ORDER}
BUYER_COLUMNS = set(STANDARD_COLUMNS_BY_ROLE["BUYER"])
CAPACITY_MANAGER_COLUMNS = set(STANDARD_COLUMNS_BY_ROLE["CAPACITY_MANAGER"])
SQD_COLUMNS = set(STANDARD_COLUMNS_BY_ROLE["SQD"])


def get_columns_by_owner(owner: str) -> List[str]:
    owner_upper = str(owner).strip().upper()
    return list(STANDARD_COLUMNS_BY_ROLE.get(owner_upper, []))


def get_column_label(column_key: str) -> str:
    return str(column_key)


def get_auto_co(part_number: Optional[str] = None, cross_project_set: Optional[Set[str]] = None) -> str:
    if not part_number:
        return "New"

    normalized_part_number = str(part_number).strip()
    if not normalized_part_number:
        return "New"

    if cross_project_set is not None:
        return "CO" if normalized_part_number in cross_project_set else "New"

    return "CO" if any(character.isdigit() for character in normalized_part_number) else "New"


def get_auto_columns(part_number: Optional[str] = None, cross_project_set: Optional[Set[str]] = None) -> str:
    return get_auto_co(part_number, cross_project_set)


def is_auto_column(column_key: str) -> bool:
    return column_key in AUTO_COLUMNS


def is_fixed_column(column_key: str) -> bool:
    return column_key in FIXED_COLUMNS
