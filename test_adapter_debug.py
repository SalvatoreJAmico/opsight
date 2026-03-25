#!/usr/bin/env python
"""Debug adapter with actual sample data."""

import pandas as pd
from modules.adapter.adapter import normalize_record, to_canonical_schema

print("=== Testing JSON ===")
json_df = pd.read_json('data/opsight_sample_customers.json')
print("DataFrame columns:", json_df.columns.tolist())
print("DataFrame shape:", json_df.shape)

normalized = normalize_record(json_df)
print("\nNormalized:")
print("  entity_id_cols:", normalized["entity_id_cols"])
print("  timestamp_cols:", normalized["timestamp_cols"])
print("  feature_cols:", normalized["feature_cols"])

try:
    canonical = to_canonical_schema(normalized)
    print("\n✓ Canonical records created successfully!")
    print("First record:", canonical[0] if canonical else "No records")
except Exception as e:
    print(f"\n✗ ERROR in to_canonical_schema: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing XLSX ===")
xlsx_df = pd.read_excel('data/opsight_sample_finance.xlsx')
print("DataFrame columns:", xlsx_df.columns.tolist())
print("DataFrame shape:", xlsx_df.shape)

normalized = normalize_record(xlsx_df)
print("\nNormalized:")
print("  entity_id_cols:", normalized["entity_id_cols"])
print("  timestamp_cols:", normalized["timestamp_cols"])
print("  feature_cols:", normalized["feature_cols"])

try:
    canonical = to_canonical_schema(normalized)
    print("\n✓ Canonical records created successfully!")
    print("First record:", canonical[0] if canonical else "No records")
except Exception as e:
    print(f"\n✗ ERROR in to_canonical_schema: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing CSV ===")
csv_df = pd.read_csv('data/opsight_sample_sales.csv')
print("DataFrame columns:", csv_df.columns.tolist())
print("DataFrame shape:", csv_df.shape)

normalized = normalize_record(csv_df)
print("\nNormalized:")
print("  entity_id_cols:", normalized["entity_id_cols"])
print("  timestamp_cols:", normalized["timestamp_cols"])
print("  feature_cols:", normalized["feature_cols"])

try:
    canonical = to_canonical_schema(normalized)
    print("\n✓ Canonical records created successfully!")
    print("First record:", canonical[0] if canonical else "No records")
except Exception as e:
    print(f"\n✗ ERROR in to_canonical_schema: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
