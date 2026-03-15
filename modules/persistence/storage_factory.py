from modules.persistence.local_storage import LocalStorage
from modules.persistence.parquet_storage import ParquetStorage


class StorageFactory:
    """
    Factory responsible for returning the correct storage backend.
    """

    @staticmethod
    def create_storage(config):
        backend = config.backend

        if backend == "json":
            return LocalStorage()

        if backend == "parquet":
            return ParquetStorage()

        raise ValueError(f"Unsupported storage backend: {backend}")