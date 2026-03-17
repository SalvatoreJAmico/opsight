import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.intelligence.anomaly_detection import detect_anomalies
from modules.intelligence.evaluation import evaluate
from modules.intelligence.feature_engineering import build_features
from modules.intelligence.scoring import score_records


class TestFeatureEngineering(unittest.TestCase):
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
                "features": {"amount": 20.0, "count": 4},
                "metadata": {"source": "sample"},
            },
        ]

    def test_build_features_canonical_records_shape(self):
        df = build_features(self.records)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertListEqual(df["entity_id"].tolist(), ["cust-001", "cust-002"])
        self.assertListEqual(
            df["timestamp"].tolist(),
            ["2026-03-15T12:00:00", "2026-03-15T12:05:00"],
        )

        self.assertIn("amount", df.columns)
        self.assertIn("count", df.columns)
        self.assertIn("feature_count", df.columns)
        self.assertIn("feature_sum", df.columns)

        self.assertEqual(df.loc[0, "feature_count"], 2)
        self.assertEqual(df.loc[1, "feature_count"], 2)
        self.assertEqual(df.loc[0, "feature_sum"], 12.0)
        self.assertEqual(df.loc[1, "feature_sum"], 24.0)

    def test_build_features_with_normalize_scales_numeric_columns(self):
        df = build_features(self.records, normalize=True)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn("entity_id", df.columns)
        self.assertIn("timestamp", df.columns)

        for col in ["amount", "count"]:
            self.assertGreaterEqual(float(df[col].min()), 0.0)
            self.assertLessEqual(float(df[col].max()), 1.0)

        self.assertEqual(df.loc[0, "amount"], 0.0)
        self.assertEqual(df.loc[1, "amount"], 1.0)
        self.assertEqual(df.loc[0, "count"], 0.0)
        self.assertEqual(df.loc[1, "count"], 1.0)


class TestAnomalyDetection(unittest.TestCase):
    def test_detect_anomalies_returns_dataframe_with_expected_columns(self):
        records = [
            {
                "entity_id": "cust-001",
                "timestamp": "2026-03-15T12:00:00",
                "features": {"amount": 10.0, "count": 1},
                "metadata": {},
            },
            {
                "entity_id": "cust-002",
                "timestamp": "2026-03-15T12:05:00",
                "features": {"amount": 11.0, "count": 1},
                "metadata": {},
            },
            {
                "entity_id": "cust-003",
                "timestamp": "2026-03-15T12:10:00",
                "features": {"amount": 12.0, "count": 1},
                "metadata": {},
            },
            {
                "entity_id": "cust-004",
                "timestamp": "2026-03-15T12:15:00",
                "features": {"amount": 13.0, "count": 1},
                "metadata": {},
            },
            {
                "entity_id": "cust-005",
                "timestamp": "2026-03-15T12:20:00",
                "features": {"amount": 100.0, "count": 1},
                "metadata": {},
            },
        ]

        df = detect_anomalies(records)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("is_anomaly", df.columns)
        self.assertIn("anomaly_score", df.columns)
        self.assertTrue(df["is_anomaly"].any())

    def test_detect_anomalies_empty_input_returns_empty_dataframe(self):
        df = detect_anomalies([])

        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)


class TestScoring(unittest.TestCase):
    def test_score_records_adds_severity_and_alert_with_consistent_mapping(self):
        anomaly_results = pd.DataFrame(
            [
                {"entity_id": "cust-001", "is_anomaly": False, "anomaly_score": 0.0},
                {"entity_id": "cust-002", "is_anomaly": True, "anomaly_score": 1.0},
                {"entity_id": "cust-003", "is_anomaly": True, "anomaly_score": 2.0},
                {"entity_id": "cust-004", "is_anomaly": True, "anomaly_score": 3.0},
            ]
        )

        scored = score_records(anomaly_results)

        self.assertIn("severity", scored.columns)
        self.assertIn("alert", scored.columns)

        self.assertEqual(scored.loc[0, "severity"], "low")
        self.assertEqual(scored.loc[1, "severity"], "medium")
        self.assertEqual(scored.loc[2, "severity"], "high")
        self.assertEqual(scored.loc[3, "severity"], "critical")

        self.assertEqual(scored.loc[0, "alert"], "OK")
        self.assertEqual(scored.loc[1, "alert"], "ALERT")
        self.assertEqual(scored.loc[2, "alert"], "ALERT")
        self.assertEqual(scored.loc[3, "alert"], "ALERT")


class TestEvaluation(unittest.TestCase):
    def test_evaluate_returns_expected_metrics_keys(self):
        scored_records = pd.DataFrame(
            [
                {"entity_id": "cust-001", "is_anomaly": False, "anomaly_score": 0.0, "severity": "low"},
                {"entity_id": "cust-002", "is_anomaly": True, "anomaly_score": 1.0, "severity": "medium"},
                {"entity_id": "cust-003", "is_anomaly": True, "anomaly_score": 3.0, "severity": "critical"},
            ]
        )

        result = evaluate(scored_records)

        self.assertIsInstance(result, dict)
        self.assertIn("total_records", result)
        self.assertIn("anomaly_count", result)
        self.assertIn("anomaly_rate", result)
        self.assertIn("severity_breakdown", result)
        self.assertIn("score_distribution", result)

        self.assertEqual(result["total_records"], 3)
        self.assertEqual(result["anomaly_count"], 2)
        self.assertAlmostEqual(result["anomaly_rate"], 2 / 3)
        self.assertEqual(result["severity_breakdown"]["critical"], 1)
        self.assertEqual(result["score_distribution"]["3.0"], 1)

    def test_evaluate_empty_dataframe_returns_zero_and_empty_metrics(self):
        result = evaluate(pd.DataFrame())

        self.assertEqual(
            result,
            {
                "total_records": 0,
                "anomaly_count": 0,
                "anomaly_rate": 0.0,
                "severity_breakdown": {},
                "score_distribution": {},
            },
        )


if __name__ == "__main__":
    unittest.main()
