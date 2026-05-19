"""
Utilitaire de mapping colonnes - Convertir entre les formats
"""

# Mapping: snake_case CMFRecord → PascalCase Excel
RECORD_TO_EXCEL = {
    "apqp": "APQP",
    "partname": "Partname",
    "commodity": "Commodity",
    "new_co": "NewCO",
    "use_case": "UseCase",
    "part_number": "PartNumber",
    "quantity": "Quantity",
    "supplier_name": "SupplierName",
    "manufacturing_cofor": "ManufacturingCOFOR",
    "production_location": "ProductionLocation",
    "buyer": "Buyer",
    "purchasing_manager": "PurchasingManager",
    "gm": "GM",
    "sque": "SQE",
    "scr": "SCR",
    "link_to_doc_info": "LinkToDocInfo",
    "gst_no": "GSTNo",
    "mix": "Mix",
    "capacity_source": "CapacitySource",
    "calculated_weekly_capacity": "CalculatedWeeklyCapacity",
    "cm_comment": "CMComment",
    "weekly_capacity_to_measure": "WeeklyCapacityToMeasure",
    "k9_sck": "K9SCK",
    "cat1_forecasted_date": "CAT1ForecastedDate",
    "cat2_forecasted_date": "CAT2ForecastedDate",
    "cat3_forecasted_date": "CAT3ForecastedDate",
    "cat1_type": "CAT1Type",
    "cat2_type": "CAT2Type",
    "cat3_type": "CAT3Type",
    "weekly_capacity_measured": "WeeklyCapacityMeasured",
    "estimated_target": "EstimatedTarget",
    "cat1_evaluation": "CAT1Evaluation",
    "cat2_evaluation": "CAT2Evaluation",
    "cat3_evaluation": "CAT3Evaluation",
    "shared_folder": "SharedFolder",
    "sqd_comment": "SQDComment",
    "sque_team": "SQETeam",
    "status": "Status",
    "last_updated": "LastUpdated",
    "updated_by": "UpdatedBy",
}

# Mapping inverse
EXCEL_TO_RECORD = {v: k for k, v in RECORD_TO_EXCEL.items()}

def normalize_dataframe_columns(df, direction="to_excel"):
    """
    Normalise les colonnes d'un DataFrame
    direction: 'to_excel' (snake_case → PascalCase) ou 'to_record' (PascalCase → snake_case)
    """
    mapping = RECORD_TO_EXCEL if direction == "to_excel" else EXCEL_TO_RECORD
    
    # Rename columns using the mapping
    rename_dict = {col: mapping.get(col, col) for col in df.columns}
    return df.rename(columns=rename_dict)


def record_dict_to_excel(record_dict):
    """Convertit un dict CMFRecord à un dict Excel"""
    return {RECORD_TO_EXCEL.get(k, k): v for k, v in record_dict.items() if k != 'row_id'}
