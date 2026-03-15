class StorageInterface:
    """
    Interface for storage operations.
    """

    def save_records(self, records):
        """
        Save validated canonical records.
        Implementation will be added in Phase 3.
        """
        raise NotImplementedError("save_records() must be implemented by subclass")

    def load_records(self):
        """
        Load records from storage.
        Implementation will be added in Phase 3.
        """
        raise NotImplementedError("load_records() must be implemented by subclass")   

