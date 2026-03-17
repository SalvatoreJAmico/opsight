from typing import Any, Dict, List


def score_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stub scoring function for Phase 7.

    Accepts records and returns them unchanged for now.
    Later phases will attach scores and alert levels.
    """
    if not isinstance(records, list):
        raise ValueError("records must be a list")

    return records