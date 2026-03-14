"""
Opsight Adapter Layer
Responsible for converting raw data sources into the canonical schema.
"""

from pathlib import Path
import pandas as pd

def detect_format(source_path: str) -> str:
    """
    Detect the format of the incoming data source.

    Possible outputs:
    csv
    json
    excel
    parquet
    sql
    """

    if source_path.startswith("sql://"):
        return "sql"

    path = Path(source_path)

    with open(source_path, "rb") as f:
        header = f.read(4)

    if b"{" in header or b"[" in header:
        return "json"
    elif b"PAR1" in header:
        return "parquet"
    elif b"PK" in header:
        return "zip/excel"
    else: 
        with open(source_path, "r", encoding= "utf-8", errors="ignore")as f:
            sample_text = f.readline()

        if "," in sample_text:
            return "csv"
        elif "\t" in sample_text:
            return "tsv"
        else: return "text"



def load_source(source_path: str, source_format: str):
    """
    Load the source data depending on detected format.
    Should return a dataframe-like structure.
    """
    if source_format == "sql":
       # TODO: Send to sql adapter.
        return pd.DataFrame()

    df = pd.DataFrame()
  
    if source_format == "csv":
        df = pd.read_csv(source_path)
    elif source_format == "tsv":
        df = pd.read_csv(source_path, sep="\t")
    elif source_format == "json":
        df = pd.read_json(source_path)
    elif source_format == "parquet":
        df = pd.read_parquet(source_path)
    elif source_format == "excel":
        df = pd.read_excel(source_path)
    else:
         raise ValueError(f"Unsupported source format: {source_format}")

    return df


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
            "metadata": {}
            }
        canonical.append(canonical_data)
    

    return canonical