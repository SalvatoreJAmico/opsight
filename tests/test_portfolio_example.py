"""Focused offline regression checks for the portfolio demonstration."""
import json
import tempfile
import unittest
from pathlib import Path
from examples.portfolio.run_example import run


class TestPortfolioExample(unittest.TestCase):
    def test_validation_persistence_and_anomaly_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            summary = run(output)
            self.assertEqual(summary['input_records'], 14)
            self.assertEqual(summary['accepted_records'], 11)
            self.assertEqual(summary['rejected_records'], 3)
            self.assertEqual(summary['persisted_records'], 11)
            self.assertTrue(summary['json_round_trip_equal'])
            self.assertEqual(summary['anomaly_entity_ids'], ['synthetic-011'])
            rejected = json.loads((output / 'rejected.json').read_text())
            self.assertEqual([r['errors'] for r in rejected], [
                ['Missing entity_id'], ['Missing timestamp'], ['Features must be a dictionary']])
            predictions = json.loads((output / 'anomalies.json').read_text())
            self.assertEqual(predictions['records'][-1]['anomaly_score'], 3.1597)

    def test_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                run(directory)

    def test_repeated_runs_have_same_functional_results(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            run(first)
            run(second)
            for name in ['accepted.json', 'rejected.json', 'anomalies.json']:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
