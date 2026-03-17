import os

from modules.config.runtime_config import load_runtime_config


class StorageConfig:
    """
    Environment-aware configuration for persistence backend.
    Backward-compatible with older code that passes backend explicitly.
    """

    def __init__(self, backend=None):
        runtime_config = load_runtime_config()

        self.app_env = runtime_config.app_env
        self.backend = backend or runtime_config.persistence_mode
        self.storage_path = runtime_config.storage_path

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