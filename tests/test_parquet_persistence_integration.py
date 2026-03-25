"""
Integration test: Parquet ingestion with persistence
Validates the complete pipeline from parquet ingestion to JSON persistence
with pandas Timestamp handling.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from modules.persistence.local_storage import LocalStorage


class TestParquetToPersistencePipeline(unittest.TestCase):
    """Integration test for parquet data with timestamps through persistence"""

    def test_parquet_with_timestamps_persists_to_json(self):
        """
        Simulate parquet ingestion that produces records with pandas Timestamps,
        then verify they persist correctly to JSON.
        """
        # Simulate data loaded from parquet with pandas Timestamps
        parquet_df = pd.DataFrame({
            "customer_id": ["cust-001", "cust-002", "cust-003"],
            "purchase_date": pd.to_datetime([
                "2026-03-15 10:30:00",
                "2026-03-15 11:45:00",
                "2026-03-15 14:20:00"
            ]),
            "amount": [100.0, 250.5, 75.25]
        })

        # Simulate adapter converting to canonical schema
        # (adapter normalizes and includes pandas Timestamp as-is)
        canonical_records = []
        for _, row in parquet_df.iterrows():
            canonical_records.append({
                "entity_id": row["customer_id"],
                "timestamp": row["purchase_date"],  # pandas.Timestamp, not string
                "features": {"amount": row["amount"]},
                "metadata": {"source": "parquet_dataset"}
            })

        # Save to JSON using LocalStorage
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")
            
            # This should NOT raise "Timestamp is not JSON serializable" error
            storage.save_records(canonical_records)
            
            # Verify we can read it back
            loaded_records = storage.load_records()
            
            # Verify the data
            self.assertEqual(len(loaded_records), 3)
            self.assertEqual(loaded_records[0]["entity_id"], "cust-001")
            # Timestamp should be converted to ISO string
            self.assertEqual(loaded_records[0]["timestamp"], "2026-03-15T10:30:00")
            self.assertEqual(loaded_records[1]["timestamp"], "2026-03-15T11:45:00")
            self.assertEqual(loaded_records[2]["timestamp"], "2026-03-15T14:20:00")
            # Features should be intact
            self.assertEqual(loaded_records[0]["features"]["amount"], 100.0)
            self.assertEqual(loaded_records[1]["features"]["amount"], 250.5)


if __name__ == "__main__":
    unittest.main()
