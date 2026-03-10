

# PS-003: Implement ingestion record validation
# Validates that a record contains the required fields defined in the ingestion data contract.

def validate_record(record):
    required_fields = ['timestamp', 'source', 'event_type']
    for field in required_fields:
        if field not in record:
            return False
    return True
