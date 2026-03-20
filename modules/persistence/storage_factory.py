from modules.persistence.local_storage import LocalStorage
from modules.persistence.parquet_storage import ParquetStorage


class StorageFactory:
    """
    Factory responsible for returning the correct storage backend.
    """

    @staticmethod
    def create_storage(config):
        backend = getattr(config, "persistence_mode", None) or getattr(config, "backend", None)
        storage_path = config.storage_path

        if not backend:
            raise ValueError("Storage configuration must define persistence_mode or backend")

        if backend == "json":
            return LocalStorage(storage_path=storage_path)

        if backend == "parquet":
            return ParquetStorage(storage_path=storage_path)

        raise ValueError(f"Unsupported storage backend: {backend}")