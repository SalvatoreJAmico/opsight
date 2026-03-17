import os
from pathlib import Path
import pandas as pd

from modules.persistence.storage_interface import StorageInterface


class ParquetStorage(StorageInterface):
    """
    Parquet storage backend for canonical records.
    """

    def __init__(self, storage_dir=None, filename=None, storage_path=None):
        if storage_path is None:
            if storage_dir is not None and filename is not None:
                storage_path = str(Path(storage_dir) / filename)
            else:
                storage_path = os.getenv("STORAGE_PATH")

        if not storage_path:
            raise RuntimeError("Missing required environment variable: STORAGE_PATH")

        resolved_path = Path(storage_path)
        self.storage_dir = str(resolved_path.parent)
        self.filepath = str(resolved_path)

        os.makedirs(self.storage_dir, exist_ok=True)

    def save_records(self, records: list):
        df = pd.DataFrame(records)
        df.to_parquet(self.filepath, index=False)

    def load_records(self):
        if not os.path.exists(self.filepath):
            return []

        df = pd.read_parquet(self.filepath)
        return df.to_dict(orient="records")