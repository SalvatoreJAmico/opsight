def detect_duplicates(records):
    seen = set()
    duplicates = []
    found = False

    for index, record in enumerate(records):
        entity_id = record.get("entity_id")
        timestamp = record.get("timestamp")

        if entity_id is None or timestamp is None:
            continue

        test_key = (entity_id, timestamp)

        if test_key in seen:
            found = True
            duplicates.append({
                "record_index": index,
                "entity_id": entity_id,
                "timestamp": timestamp,
            })
        else:
            seen.add(test_key)

    return {
        "duplicates_found": found,
        "duplicate_records": duplicates,
    }