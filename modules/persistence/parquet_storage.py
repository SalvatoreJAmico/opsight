import os
import pandas as pd

from modules.persistence.storage_interface import StorageInterface


class ParquetStorage(StorageInterface):
    """
    Parquet storage backend for canonical records.
    """

    def __init__(self, storage_dir="data", filename="records.parquet"):
        self.storage_dir = storage_dir
        self.filepath = os.path.join(storage_dir, filename)

        os.makedirs(self.storage_dir, exist_ok=True)

    def save_records(self, records: list):
        df = pd.DataFrame(records)
        df.to_parquet(self.filepath, index=False)

    def load_records(self):
        if not os.path.exists(self.filepath):
            return []

        df = pd.read_parquet(self.filepath)
        return df.to_dict(orient="records")