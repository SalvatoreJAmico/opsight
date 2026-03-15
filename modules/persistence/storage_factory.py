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

        # TODO
        # if backend == "parquet", return the correct storage implementation

        if backend is "parquet":
            return ParquetStorage()

        raise ValueError(f"Unsupported storage backend: {backend}")