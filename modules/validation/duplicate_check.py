def detect_duplicates(records):
    seen = set()
    duplicates = []
    found = False
    
    for index, record in enumerate(records):

        test_key = (record["entity_id"],record["timestamp"])

        if test_key in seen:
            found = True
            duplicates.append({
                "record_index": index,
            "entity_id": record["entity_id"],
            "timestamp": record["timestamp"]
            })

        else:
            seen.add(test_key)

    return ({
        "duplicates_found":found,
        "duplicate_records":duplicates
    })