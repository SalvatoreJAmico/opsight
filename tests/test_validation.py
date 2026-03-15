import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.validation.duplicate_check import detect_duplicates
from modules.validation.validator import validate_canonical_record


class TestValidationLayer(unittest.TestCase):
    def test_valid_record_passes(self):
        record = {
            "entity_id": "cust-001",
            "timestamp": "2026-03-15T12:00:00",
            "features": {"amount": 100.0},
            "metadata": {"source": "sample"},
        }

        result = validate_canonical_record(record)

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])

    def test_missing_entity_id_fails(self):
        record = {
            "timestamp": "2026-03-15T12:00:00",
            "features": {"amount": 100.0},
            "metadata": {"source": "sample"},
        }

        result = validate_canonical_record(record)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("Missing entity_id", result["errors"])

    def test_missing_timestamp_fails(self):
        record = {
            "entity_id": "cust-001",
            "features": {"amount": 100.0},
            "metadata": {"source": "sample"},
        }

        result = validate_canonical_record(record)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("Missing timestamp", result["errors"])

    def test_features_not_dict_fails(self):
        record = {
            "entity_id": "cust-001",
            "timestamp": "2026-03-15T12:00:00",
            "features": ["not", "a", "dict"],
            "metadata": {"source": "sample"},
        }

        result = validate_canonical_record(record)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("Features must be a dictionary", result["errors"])

    def test_duplicate_record_detection_works(self):
        records = [
            {
                "entity_id": "cust-001",
                "timestamp": "2026-03-15T12:00:00",
                "features": {"amount": 100.0},
                "metadata": {},
            },
            {
                "entity_id": "cust-001",
                "timestamp": "2026-03-15T12:00:00",
                "features": {"amount": 125.0},
                "metadata": {},
            },
        ]

        result = detect_duplicates(records)

        self.assertTrue(result["duplicates_found"])
        self.assertEqual(len(result["duplicate_records"]), 1)
        self.assertEqual(result["duplicate_records"][0]["record_index"], 1)


if __name__ == "__main__":
    unittest.main()