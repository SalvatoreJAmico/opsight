from modules.persistence.storage_factory import StorageFactory


class PersistenceManager:
    """
    Manages record persistence using the configured storage backend.
    """

    def __init__(self, config):
        self.storage = StorageFactory.create_storage(config)

    def persist_records(self, records):
        self.storage.save_records(records)