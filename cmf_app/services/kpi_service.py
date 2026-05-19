"""
KPI Service - Calculate R/O/G metrics and missing capacity indicators.

Business Rules:
- R/O/G determination follows hierarchy: R > O > G
- Missing detection: NULL, '', '0', '0.0', 'nan', 'NaN', 'NA', 'None', or NaN
- Numeric columns should be saved as empty string, not 'nan'
"""

import pandas as pd
from typing import Tuple, Dict


def _clean(val) -> str:
    """
    Normalize a value to one of: '', 'R', 'O', 'G'.
    Handles NaN, 'nan', 'NA', 'None' as empty.
    
    Args:
        val: Any value (can be NaN, str, int, float)
        
    Returns:
        Cleaned string: '', 'R', 'O', or 'G'
    """
    if pd.isna(val):
        return ""
    
    val_str = str(val).strip().upper()
    
    # Treat string representations of missing as empty
    if val_str in ("NAN", "NA", "NONE", ""):
        return ""
    
    return val_str if val_str in ("R", "O", "G") else ""


def _clean_num(series: pd.Series) -> pd.Series:
    """
    Clean numeric series: converts NaN, 'nan', '', etc. to empty string.
    Useful for detecting missing capacity values.
    
    Args:
        series: Pandas series with potentially mixed types
        
    Returns:
        Cleaned series with '' for missing values
    """
    return (
        series.replace(["nan", "NaN", "NA", "None"], "")
               .fillna("")
               .astype(str)
               .str.strip()
    )


def compute_rag_counts(df: pd.DataFrame) -> Tuple[int, int, int]:
    """
    Compute R (Red), O (Orange), G (Green) counts from GOR and CAT columns.
    
    Business Logic:
    1. If one column is empty, use the other
    2. If both filled and identical, count once
    3. If both filled and different, apply hierarchy: R > O > G
    4. If both empty, don't count
    
    Args:
        df: DataFrame with required columns
        
    Returns:
        Tuple of (red_count, orange_count, green_count)
    """
    gor_col = "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer"
    cat_col = "CAT1/2/3 VALUATION (G;O;R)"
    
    if gor_col not in df.columns or cat_col not in df.columns:
        return 0, 0, 0
    
    gor = df[gor_col].map(_clean)
    cat = df[cat_col].map(_clean)
    
    red = orange = green = 0
    
    for g, c in zip(gor, cat):
        # Skip if both empty
        if g == "" and c == "":
            continue
        
        # Determine final color
        if g == "" or c == "":
            # One is empty, use the other
            color = g or c
        elif g == c:
            # Both same, use that color
            color = g
        else:
            # Both different, apply hierarchy R > O > G
            if "R" in (g, c):
                color = "R"
            elif "O" in (g, c):
                color = "O"
            else:
                color = "G"
        
        # Increment counter
        if color == "R":
            red += 1
        elif color == "O":
            orange += 1
        elif color == "G":
            green += 1
    
    return int(red), int(orange), int(green)


def compute_missing_kpis(df: pd.DataFrame) -> Dict[str, int]:
    """
    Compute counts of missing capacity indicators.
    
    Missing Detection: NULL, '', '0', '0.0', 'nan', 'NaN', 'NA', 'None', or NaN
    
    Args:
        df: DataFrame with required columns
        
    Returns:
        Dict with keys: missing_contracted, missing_measured, missing_requested
    """
    def _is_missing(series: pd.Series) -> pd.Series:
        """
        Check if values are missing.
        Treats NULL, '', '0', '0.0', 'nan', 'NaN', 'NA', 'None', NaN as missing.
        """
        s = _clean_num(series)  # Normalize all variants of missing
        return (s == "") | (s.isin(["0", "0.0"]))
    
    contracted_col = "WEEKLY CAPACITY CONTRACTED (Parts/Week)"
    measured_col = "WEEKLY CAPACITY MEASURED"
    requested_col = "LAST WEEKLY CAPACITY REQUESTED"
    
    result = {
        "missing_contracted": 0,
        "missing_measured": 0,
        "missing_requested": 0,
    }
    
    if contracted_col in df.columns:
        result["missing_contracted"] = int(_is_missing(df[contracted_col]).sum())
    
    if measured_col in df.columns:
        result["missing_measured"] = int(_is_missing(df[measured_col]).sum())
    
    if requested_col in df.columns:
        result["missing_requested"] = int(_is_missing(df[requested_col]).sum())
    
    return result
