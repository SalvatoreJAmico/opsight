import json
import os
from pathlib import Path
from datetime import datetime, date

import pandas as pd

from modules.persistence.storage_interface import StorageInterface
from modules.persistence.storage_error import StorageError


class _JsonWithPandasEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles pandas datetime types.
    Converts pandas Timestamp, datetime, and date objects to ISO format strings.
    """
    def default(self, obj):
        # Handle pandas Timestamp and datetime objects
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        # Handle date objects
        if isinstance(obj, date):
            return obj.isoformat()
        # Fall back to default encoder for other types
        return super().default(obj)

class LocalStorage(StorageInterface):
    """
    Local JSON storage backend for canonical records.
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
        try:
            with open(self.filepath, "w") as f:
                json.dump(records, f, indent=2, cls=_JsonWithPandasEncoder)

        except Exception as e:
            raise StorageError(f"Failed to save records: {e}")

    def load_records(self):
        if not os.path.exists(self.filepath):
            return []

        with open(self.filepath, "r") as f:
            return json.load(f)
        
    def get_records_by_entity(self, entity_id):
        records = self.load_records()
        return [record for record in records if str(record.get("entity_id")) == str(entity_id)]