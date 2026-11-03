"""Regression coverage for stale data, field identity, and forecast correctness."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for key, value in {
    "APP_ENV": "dev", "APP_VERSION": "0.1.0-test", "PORT": "8000",
    "UPLOAD_ACCESS_CODE": "test-access-code", "PERSISTENCE_MODE": "json",
    "STORAGE_PATH": "data/test-records.json", "LOG_LEVEL": "INFO",
    "ALLOW_LOCAL_FALLBACK": "true", "API_BASE_URL": "http://api-test.local:8000",
    "INPUT_SOURCE_PATH": "data/opsight_sample_sales.csv",
    "PIPELINE_SUMMARY_PATH": "reports/pipeline_run_summary.json",
    "CORS_ALLOWED_ORIGINS": "http://localhost:5173",
}.items():
    os.environ.setdefault(key, value)

from modules.api.app import app
from modules.api import session_state as state
from modules.ml.feature_pipeline import build_feature_dataset
from modules.ml.prediction_moving_average import MovingAverageModel
from modules.ml.prediction_regression import LinearRegressionModel
from modules.ml.schemas import FeatureRecord
from modules.persistence.local_storage import LocalStorage

ENDPOINTS = ["/ml/anomaly/zscore", "/ml/anomaly/isolation-forest", "/ml/anomaly/kmeans",
             "/ml/prediction/regression", "/ml/prediction/moving-average"]


@pytest.fixture(autouse=True)
def clean_state():
    state.reset_session_state()
    yield
    state.reset_session_state()


@pytest.fixture
def dataset(tmp_path):
    path = tmp_path / "records.json"
    storage = LocalStorage(storage_path=str(path))
    with patch("modules.api.routes.ml.StorageConfig") as config:
        config.return_value.storage_path = str(path)
        yield storage


def records(values, field="value"):
    return [{"entity_id": str(i), "timestamp": f"2026-01-{i+1:02d}", "features": {field: value}, "metadata": {}}
            for i, value in enumerate(values)]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("status", ["not_run", "running", "failed"])
def test_models_refuse_prior_data_for_unfinished_selected_dataset(dataset, endpoint, status):
    dataset.save_records(records([10, 20, 30]))
    state.set_active_dataset("sales_sql")
    state.set_pipeline_status(status)
    response = TestClient(app).get(endpoint)
    assert response.status_code == 422
    assert "has not completed" in response.json()["detail"]
    assert state.get_session_state()["anomaly_status"] == "idle"
    assert state.get_session_state()["prediction_status"] == "idle"


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_no_finite_data_is_actionable_not_internal_error(dataset, endpoint):
    dataset.save_records(records([None, float("nan"), float("inf"), -float("inf")]))
    response = TestClient(app).get(endpoint)
    assert response.status_code == 422
    assert "finite numeric" in response.json()["detail"]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_nonfinite_observations_are_excluded_and_reported(dataset, endpoint):
    dataset.save_records(records([10, float("inf"), 20, None, 30, float("nan")]))
    response = TestClient(app).get(endpoint)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["data_quality"] == {"input_records": 6, "usable_records": 3, "excluded_records": 3}
    assert [row["entity_id"] for row in data["result"] if row["entity_id"] != "future"] == ["0", "2", "4"]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_multiple_numeric_fields_require_selection_and_honor_freight(dataset, endpoint):
    rows = records([10, 20, 30, 100], field="Freight")
    for row in rows:
        row["features"] = {"ShipVia": 1, **row["features"]}
    dataset.save_records(rows)
    client = TestClient(app)
    response = client.get(endpoint)
    assert response.status_code == 422
    assert "Choose a numeric target in Charts" in response.json()["detail"]
    state.set_selected_variables("Freight", [])
    response = client.get(endpoint)
    assert response.status_code == 200, response.text
    assert response.json()["dataset_context"]["value"] == "Freight"
    if "/anomaly/" in endpoint or "moving-average" in endpoint:
        assert [row["value"] for row in response.json()["result"][:4]] == [10, 20, 30, 100]


def test_missing_selected_field_never_falls_through_to_another_measurement(dataset):
    dataset.save_records([
        {"entity_id": "first", "timestamp": "2026-01-01", "features": {"sales": None, "profit": 999}},
        {"entity_id": "second", "timestamp": "2026-01-02", "features": {"sales": 20, "profit": 888}},
    ])
    state.set_selected_variables("Sales", [])
    response = TestClient(app).get("/ml/anomaly/zscore")
    assert response.status_code == 200
    assert [(row["entity_id"], row["value"]) for row in response.json()["result"]] == [("second", 20)]
    assert response.json()["data_quality"]["excluded_records"] == 1


@pytest.mark.parametrize("target", ["not_a_column", "Category"])
def test_invalid_or_categorical_selection_is_rejected(dataset, target):
    rows = records([10, 20, 30])
    for row in rows:
        row["features"]["category"] = "A"
    dataset.save_records(rows)
    state.set_selected_variables(target, [])
    response = TestClient(app).get("/ml/anomaly/zscore")
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint,forecast", [("regression", 40), ("moving-average", 25)])
def test_forecasts_sort_timestamp_before_predicting(dataset, endpoint, forecast):
    rows = records([10, 20, 30])
    dataset.save_records([rows[2], rows[0], rows[1]])
    response = TestClient(app).get(f"/ml/prediction/{endpoint}?steps_ahead=1")
    assert response.status_code == 200
    data = response.json()["result"]
    assert [row["entity_id"] for row in data[:-1]] == ["0", "1", "2"]
    assert data[-1]["value"] == forecast


@pytest.mark.parametrize("endpoint", ["regression", "moving-average"])
@pytest.mark.parametrize("horizon", ["-1", "0", "366", "1.5"])
def test_invalid_forecast_horizons_are_rejected(dataset, endpoint, horizon):
    dataset.save_records(records([10, 20, 30]))
    response = TestClient(app).get(f"/ml/prediction/{endpoint}?steps_ahead={horizon}")
    assert 400 <= response.status_code < 500


def test_regression_needs_two_usable_points(dataset):
    dataset.save_records(records([10]))
    response = TestClient(app).get("/ml/prediction/regression")
    assert response.status_code == 422
    assert "at least 2" in response.json()["detail"]


@pytest.mark.parametrize("endpoint", ["regression", "moving-average"])
def test_forecast_invalid_timestamp_has_clear_validation_error(dataset, endpoint):
    rows = records([10, 20, 30]); rows[1]["timestamp"] = "not-a-date"
    dataset.save_records(rows)
    response = TestClient(app).get(f"/ml/prediction/{endpoint}")
    assert response.status_code == 422
    assert "valid timestamp" in response.json()["detail"]


def test_forecast_order_uses_timezone_instants_not_timestamp_strings():
    data = [FeatureRecord(entity_id="later", timestamp="2026-01-01T00:30:00Z", value=20),
            FeatureRecord(entity_id="earlier", timestamp="2026-01-01T01:00:00+01:00", value=10)]
    predictions = LinearRegressionModel().predict(data, steps_ahead=1)
    assert [row.entity_id for row in predictions] == ["earlier", "later", "future"]
    assert predictions[-1].value == 30


def test_feature_builder_normalizes_nonfinite_values():
    result = build_feature_dataset([{"entity_id": "1", "timestamp": "2026-01-01", "value": float("inf")}])
    assert result.records[0].value is None
    assert result.invalid_records == 1


def test_forecast_models_keep_values_and_identifiers_aligned_after_filtering():
    data = [FeatureRecord(entity_id="a", timestamp="2026-01-01", value=10),
            FeatureRecord(entity_id="invalid", timestamp="2026-01-02", value=None),
            FeatureRecord(entity_id="b", timestamp="2026-01-03", value=20)]
    for model in [LinearRegressionModel(), MovingAverageModel()]:
        assert [row.entity_id for row in model.predict(data)] == ["a", "b"]


def test_current_run_summary_recovers_on_reload_and_clears_on_rerun():
    state.set_active_dataset("sales_csv")
    state.set_pipeline_status("running")
    first_run = state.get_session_state()["pipeline_run_id"]
    state.set_pipeline_status("completed")
    state.set_pipeline_summary({"records_ingested": 3, "records_valid": 2, "records_invalid": 1, "records_persisted": 2})
    response = TestClient(app).get("/session/state")
    assert response.status_code == 200
    summary = response.json()["pipeline_summary"]
    assert summary["records_ingested"] == 3
    assert summary["dataset_id"] == "sales_csv"
    assert summary["pipeline_run_id"] == first_run
    state.set_anomaly_status("completed")
    state.set_prediction_status("completed")
    state.set_pipeline_status("running")
    latest = state.get_session_state()
    assert latest["pipeline_run_id"] != first_run
    assert latest["pipeline_summary"] is None
    assert latest["anomaly_status"] == latest["prediction_status"] == "idle"
    state.set_pipeline_status("failed")
    assert state.get_session_state()["pipeline_summary"] is None


def test_session_snapshot_cannot_mutate_nested_state():
    state.set_selected_variables("Sales", ["Profit"])
    snapshot = state.get_session_state()
    snapshot["selected_variables"]["compare"].append("Quantity")
    assert state.get_session_state()["selected_variables"]["compare"] == ["Profit"]


def test_successful_ingest_populates_current_run_summary():
    client = TestClient(app)
    with patch("modules.api.routes.ingest.run_pipeline", return_value={"status": "SUCCESS", "records_ingested": 4, "records_valid": 4, "records_invalid": 0, "records_persisted": 4}):
        response = client.post("/pipeline/trigger", json={"dataset_id": "sales_csv", "target": "local"})
    assert response.status_code == 200
    latest = client.get("/session/state").json()
    assert latest["pipeline_summary"]["records_persisted"] == 4
    assert latest["pipeline_summary"]["dataset_id"] == "sales_csv"
    assert latest["pipeline_summary"]["pipeline_run_id"] == latest["pipeline_run_id"]
