
from pathlib import Path
import pandas as pd


# PS-003: Implement ingestion record validation
# Validates that a record contains the required fields defined in the ingestion data contract.


def validate_record(record):
    required_fields = ["timestamp", "source", "event_type"]
    for field in required_fields:
        if field not in record:
            return False
    return True


def detect_format(source_path: str) -> str:
    """
    Detect the format of the incoming data source.
    """
    if source_path.startswith("sql://"):
        return "sql"

    path = Path(source_path)

    with open(source_path, "rb") as file_handle:
        header = file_handle.read(4)

    if b"{" in header or b"[" in header:
        return "json"
    if b"PAR1" in header:
        return "parquet"
    if b"PK" in header and path.suffix.lower() in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return "excel"

    with open(source_path, "r", encoding="utf-8", errors="ignore") as file_handle:
        sample_text = file_handle.readline()

    if "," in sample_text:
        return "csv"
    if "\t" in sample_text:
        return "tsv"
    return "text"


def load_source(source_path: str, source_format: str):
    """
    Load source data into a dataframe-like structure.
    """
    if source_format == "sql":
        return pd.DataFrame()
    if source_format == "csv":
        return pd.read_csv(source_path)
    if source_format == "tsv":
        return pd.read_csv(source_path, sep="\t")
    if source_format == "json":
        return pd.read_json(source_path)
    if source_format == "parquet":
        return pd.read_parquet(source_path)
    if source_format == "excel":
        return pd.read_excel(source_path)

    raise ValueError(f"Unsupported source format: {source_format}")
