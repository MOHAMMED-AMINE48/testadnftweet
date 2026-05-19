"""
Utility functions for finding CMF records based on business rules.
Provides validation and lookup mechanisms for APQP + PartNumber combinations.
"""

from typing import Optional, List
from models.cmf_schema import CMFRecord


def find_record_by_apqp_and_partnumber(
    records: List[CMFRecord],
    apqp: str,
    part_number: str
) -> Optional[CMFRecord]:
    """
    Find a CMF record by APQP and PartNumber combination.
    
    Args:
        records: List of CMFRecord objects to search
        apqp: APQP value to match (case-insensitive)
        part_number: PartNumber value to match (case-insensitive)
    
    Returns:
        CMFRecord if found, None otherwise
    
    Logic:
        - Typically used by Capacity Manager and SQD
        - Can only update records that were created by Buyer
        - APQP + PartNumber combination must exist in Buyer data
    """
    if not records:
        return None
    
    # Normalize inputs (trim whitespace, lowercase)
    apqp_normalized = str(apqp).strip().lower() if apqp else ""
    part_normalized = str(part_number).strip().lower() if part_number else ""
    
    if not apqp_normalized or not part_normalized:
        return None
    
    # Search for matching record
    for record in records:
        record_apqp = str(record.apqp or "").strip().lower()
        record_part = str(record.part_number or "").strip().lower()
        
        if record_apqp == apqp_normalized and record_part == part_normalized:
            return record
    
    return None


def validate_apqp_partnumber_exists(
    records: List[CMFRecord],
    apqp: str,
    part_number: str
) -> tuple[bool, Optional[CMFRecord], str]:
    """
    Validate that an APQP + PartNumber combination exists in buyer data.
    
    Args:
        records: List of CMFRecord objects
        apqp: APQP value to validate
        part_number: PartNumber value to validate
    
    Returns:
        Tuple of (is_valid: bool, record: Optional[CMFRecord], message: str)
        - is_valid: True if found, False otherwise
        - record: The found CMFRecord or None
        - message: User-friendly error/success message
    """
    # Empty check
    if not apqp or not part_number:
        return (
            False,
            None,
            "APQP and PartNumber are required. Please fill both fields."
        )
    
    # Find record
    found_record = find_record_by_apqp_and_partnumber(records, apqp, part_number)
    
    if found_record is None:
        return (
            False,
            None,
            f"❌ No Buyer record found for APQP='{apqp}' and PartNumber='{part_number}'. "
            f"Please ask Buyer to create this record first."
        )
    
    return (
        True,
        found_record,
        f"✅ Found existing Buyer record for APQP='{apqp}', PartNumber='{part_number}'"
    )


def find_records_by_apqp(
    records: List[CMFRecord],
    apqp: str
) -> List[CMFRecord]:
    """
    Find all records with a specific APQP.
    Useful for bulk operations or filtering.
    """
    if not records or not apqp:
        return []
    
    apqp_normalized = str(apqp).strip().lower()
    
    return [
        r for r in records
        if str(r.apqp or "").strip().lower() == apqp_normalized
    ]


def find_records_by_partnumber(
    records: List[CMFRecord],
    part_number: str
) -> List[CMFRecord]:
    """
    Find all records with a specific PartNumber.
    Useful for bulk operations or filtering.
    """
    if not records or not part_number:
        return []
    
    part_normalized = str(part_number).strip().lower()
    
    return [
        r for r in records
        if str(r.part_number or "").strip().lower() == part_normalized
    ]


def get_available_apqp_partnumber_combinations(
    records: List[CMFRecord]
) -> List[tuple[str, str]]:
    """
    Get all unique (APQP, PartNumber) combinations from buyer records.
    Useful for validation or autocomplete in forms.
    """
    if not records:
        return []
    
    combinations = set()
    for record in records:
        apqp = str(record.apqp or "").strip()
        part = str(record.part_number or "").strip()
        
        # Only include non-empty combinations
        if apqp and part:
            combinations.add((apqp, part))
    
    return sorted(list(combinations))
