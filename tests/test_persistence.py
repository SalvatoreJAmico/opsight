import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
        config = SimpleNamespace(backend="unsupported")

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


if __name__ == "__main__":
    unittest.main()