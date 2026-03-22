from typing import Any, Dict, List
from modules.ml.schemas import FeatureRecord, DatasetBuildResult

def build_feature_dataset(records):
    feature_records = []
    valid = 0
    invalid = 0

    for record in records:
        fr = FeatureRecord(
            entity_id=str(record.get("entity_id", "")),
            timestamp=str(record.get("timestamp", "")),
            value=_coerce_float(record.get("value")),
            label=_coerce_int(record.get("label")),
        )

        # simple validation rule (keep it minimal)
        if fr.entity_id and fr.timestamp and fr.value is not None:
            valid += 1
        else:
            invalid += 1

        feature_records.append(fr)

    return DatasetBuildResult(
        total_records=len(feature_records),
        valid_records=valid,
        invalid_records=invalid,
        records=feature_records,
    )


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None