from datetime import datetime

class StorageMetadata:
    """
    Tracks metadata about stored records.
    """

    def __init__(self):
        self.record_count = 0
        self.last_updated = None

    def update(self, records):
        self.record_count = len(records)
        self.last_updated = datetime.now(datetime.UTC)
        


        