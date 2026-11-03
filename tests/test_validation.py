import unittest

import numpy as np
import pandas as pd
from modules.adapter.adapter import adapt_records
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

    def test_required_fields_reject_scalar_missing_sentinels(self):
        for field in ("entity_id", "timestamp", "features", "metadata"):
            for missing in (None, float("nan"), np.float64("nan"), pd.NA, pd.NaT):
                with self.subTest(field=field, missing=repr(missing)):
                    record = {
                        "entity_id": "cust-001",
                        "timestamp": "2026-03-15T12:00:00",
                        "features": {"amount": 100.0},
                        "metadata": {},
                    }
                    record[field] = missing
                    result = validate_canonical_record(record)
                    self.assertEqual(result["status"], "invalid")
                    self.assertIn(f"Missing {field}", result["errors"])

    def test_valid_falsy_values_and_containers_do_not_raise(self):
        record = {"entity_id": 0, "timestamp": "2026-03-15", "features": {}, "metadata": {}}
        self.assertEqual(validate_canonical_record(record)["status"], "valid")
        for features in ([1, 2], np.array([1, 2]), pd.Series([1, 2])):
            with self.subTest(features=type(features).__name__):
                result = validate_canonical_record({**record, "features": features})
                self.assertEqual(result["errors"], ["Features must be a dictionary"])

    def test_adapter_missing_timestamp_with_both_string_inference_modes(self):
        for infer_string in (False, True):
            with self.subTest(infer_string=infer_string):
                with pd.option_context("future.infer_string", infer_string):
                    frame = pd.DataFrame([
                        {"id": "1", "order_date": "2026-01-01", "amount": 10},
                        {"id": "2", "order_date": None, "amount": 20},
                    ])
                    records = adapt_records(frame)
                self.assertEqual(validate_canonical_record(records[0])["status"], "valid")
                self.assertEqual(validate_canonical_record(records[1])["errors"], ["Missing timestamp"])

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