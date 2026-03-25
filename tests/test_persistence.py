import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from modules.persistence.local_storage import LocalStorage
from modules.persistence.persistence_manager import PersistenceManager
from modules.persistence.storage_factory import StorageFactory
from modules.persistence.storage_metadata import StorageMetadata


class TestPersistenceLayer(unittest.TestCase):
    def setUp(self):
        self.records = [
            {
                "entity_id": "cust-001",
                "timestamp": "2026-03-15T12:00:00",
                "features": {"amount": 10.0, "count": 2},
                "metadata": {"source": "sample"},
            },
            {
                "entity_id": "cust-002",
                "timestamp": "2026-03-15T12:05:00",
                "features": {"amount": 25.0, "count": 1},
                "metadata": {"source": "sample"},
            },
        ]

    def test_local_storage_saves_and_loads_records_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")

            storage.save_records(self.records)
            loaded = storage.load_records()

            self.assertTrue(Path(storage.filepath).exists())
            self.assertEqual(loaded, self.records)

    def test_local_storage_handles_empty_record_list_safely(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")

            storage.save_records([])
            loaded = storage.load_records()

            self.assertTrue(Path(storage.filepath).exists())
            self.assertEqual(loaded, [])

    def test_local_storage_load_returns_empty_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")

            loaded = storage.load_records()

            self.assertEqual(loaded, [])

    def test_storage_factory_unsupported_backend_raises_value_error(self):
        config = SimpleNamespace(backend="unsupported", storage_path="data/test-records.json")

        with self.assertRaises(ValueError) as context:
            StorageFactory.create_storage(config)

        self.assertIn("Unsupported storage backend", str(context.exception))

    def test_persistence_manager_persist_records_calls_storage_backend(self):
        mock_storage = MagicMock()

        with patch("modules.persistence.persistence_manager.StorageFactory.create_storage", return_value=mock_storage):
            manager = PersistenceManager(config=SimpleNamespace(backend="json"))
            manager.persist_records(self.records)

        mock_storage.save_records.assert_called_once_with(self.records)

    def test_storage_metadata_update_sets_record_count_and_timestamp(self):
        metadata = StorageMetadata()

        fixed_timestamp = object()
        with patch("modules.persistence.storage_metadata.datetime") as mock_datetime:
            mock_datetime.UTC = object()
            mock_datetime.now.return_value = fixed_timestamp
            metadata.update(self.records)

        self.assertEqual(metadata.record_count, 2)
        self.assertIs(metadata.last_updated, fixed_timestamp)

    def test_local_storage_serializes_pandas_timestamp_to_iso_string(self):
        """Verify that pandas Timestamp objects are converted to ISO strings for JSON serialization."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")

            # Create records with pandas Timestamp (simulating Parquet ingestion)
            timestamp = pd.Timestamp("2026-03-15 12:30:45")
            records = [
                {
                    "entity_id": "user-001",
                    "timestamp": timestamp,  # pandas Timestamp, not string
                    "features": {"amount": 100.0},
                    "metadata": {"source": "parquet"},
                }
            ]

            # Should not raise "Timestamp is not JSON serializable" error
            storage.save_records(records)
            loaded = storage.load_records()

            # Verify the timestamp was converted to ISO string
            self.assertTrue(Path(storage.filepath).exists())
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["timestamp"], "2026-03-15T12:30:45")

    def test_local_storage_serializes_datetime_objects(self):
        """Verify that datetime.datetime objects are converted to ISO strings."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")

            # Create records with datetime
            dt = datetime(2026, 3, 15, 12, 30, 45)
            records = [
                {
                    "entity_id": "user-001",
                    "timestamp": dt,
                    "features": {"amount": 100.0},
                    "metadata": {"created": date(2026, 3, 15)},
                }
            ]

            storage.save_records(records)
            loaded = storage.load_records()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["timestamp"], "2026-03-15T12:30:45")
            self.assertEqual(loaded[0]["metadata"]["created"], "2026-03-15")

