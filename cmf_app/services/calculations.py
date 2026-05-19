"""Business calculations for CMF data."""

from typing import Any, Mapping


def compute_cat_valuation(values: Mapping[str, Any]) -> str:
    """Return R, O, G, or empty string from the CAT capacity rule.

    Rule:
    - G: measured capacity is greater than requested capacity
    - O: measured capacity is approximately equal to requested capacity
    - R: measured capacity is lower than requested capacity
    """

    measured_raw = values.get("WEEKLY CAPACITY MEASURED")
    requested_raw = values.get("LAST WEEKLY CAPACITY REQUESTED")
    if measured_raw in (None, "", 0, "0") or requested_raw in (None, "", 0, "0"):
        return ""

    try:
        requested = float(requested_raw)
        measured = float(measured_raw)
    except (TypeError, ValueError):
        return ""

    tolerance = max(abs(requested) * 0.05, 1e-9)
    if abs(measured - requested) <= tolerance:
        return "O"
    if measured > requested:
        return "G"
    return "R"
