class StorageConfig:
    """
    Configuration for persistence backend.
    """

    def __init__(self, backend="json"):
        self.backend = backend

    def __str__(self):
        return f"StorageConfig(backend={self.backend})"
