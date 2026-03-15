"""
Opsight Adapter Layer
Responsible for transforming source records into the canonical schema.
"""


def normalize_record(record):
    """
    Normalize a raw record from the dataset.

    This prepares the record for conversion to the canonical schema.
    """
    record.columns = record.columns.str.strip().str.lower()

    entity_id_cols = []
    timestamp_cols = []
    feature_cols = []

    for col in record.columns:
        if "id" in col:
            entity_id_cols.append(col)
        elif "time" in col or "date" in col:
            timestamp_cols.append(col)
        else:
            feature_cols.append(col)

    return {
        "entity_id_cols": entity_id_cols,
        "timestamp_cols": timestamp_cols,
        "feature_cols": feature_cols,
        "data": record,
    }


def to_canonical_schema(record):
    """
    Convert a normalized record into the Opsight canonical schema.

    Target structure:
        entity_id
        timestamp
        features
        metadata
    """
    canonical = []

    for _, row in record["data"].iterrows():
        entity = record["entity_id_cols"][0]
        time = record["timestamp_cols"][0]

        entity_id = row[entity]
        timestamp = row[time]

        features = {}
        for col in record["feature_cols"]:
            features[col] = row[col]

        canonical_data = {
            "entity_id": entity_id,
            "timestamp": timestamp,
            "features": features,
            "metadata": {},
        }
        canonical.append(canonical_data)

    return canonical


def adapt_records(records):
    """
    Transform raw ingested records into canonical records.
    """
    normalized = normalize_record(records)
    return to_canonical_schema(normalized)