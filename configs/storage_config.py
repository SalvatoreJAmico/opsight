class StorageConfig:
    """
    Configuration for persistence backend.
    """

    def __init__(self, backend="json"):
        # TODO
        # store the backend type on the object
        # expected values later: "json", "parquet"
        self.backend = backend
    def __str__(self):        
        return f"StorageConfig(backend={self.backend})"
    