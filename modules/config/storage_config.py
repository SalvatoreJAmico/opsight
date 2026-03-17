import os


class StorageConfig:
    """
    Environment-aware configuration for persistence backend.
    Backward-compatible with older code that passes backend explicitly.
    """

    def __init__(self, backend=None):
        self.app_env = os.getenv("APP_ENV", "development")
        self.backend = backend or os.getenv("STORAGE_BACKEND", "json")
        self.storage_path = os.getenv("STORAGE_PATH", "data/records.json")

        self.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        self.azure_storage_container = os.getenv("AZURE_STORAGE_CONTAINER", "")
        self.azure_key_vault_url = os.getenv("AZURE_KEY_VAULT_URL", "")

    def __str__(self):
        return (
            f"StorageConfig(env={self.app_env}, "
            f"backend={self.backend}, "
            f"path={self.storage_path})"
        )

    def to_dict(self):
        return {
            "app_env": self.app_env,
            "backend": self.backend,
            "storage_path": self.storage_path,
            "azure_storage_connection_string": self.azure_storage_connection_string,
            "azure_storage_container": self.azure_storage_container,
            "azure_key_vault_url": self.azure_key_vault_url,
        }