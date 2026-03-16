import json
import os

from modules.persistence.storage_interface import StorageInterface
from modules.persistence.storage_error import StorageError

class LocalStorage(StorageInterface):
    """
    Local JSON storage backend for canonical records.
    """

    def __init__(self, storage_dir="data", filename="records.json"):
        self.storage_dir = storage_dir
        self.filepath = os.path.join(storage_dir, filename)

        os.makedirs(self.storage_dir, exist_ok=True)

    def save_records(self, records: list):
        try:
            with open(self.filepath, "w") as f:
                json.dump(records, f, indent=2)

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