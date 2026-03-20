import os
import sys
import time
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("APP_VERSION", "0.1.0-test")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("UPLOAD_ACCESS_CODE", "test-access-code")
os.environ.setdefault("PERSISTENCE_MODE", "json")
os.environ.setdefault("STORAGE_PATH", "data/test-records.json")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("ALLOW_LOCAL_FALLBACK", "true")
os.environ.setdefault("API_BASE_URL", "http://api-test.local:8000")
os.environ.setdefault("INPUT_SOURCE_PATH", "data/opsight_sample_sales.csv")
os.environ.setdefault("PIPELINE_SUMMARY_PATH", "reports/pipeline_run_summary.json")

import modules.api.app as api_app_module


client = TestClient(api_app_module.app)

CHART_ENDPOINTS = {
    "/charts/histogram": {
        "plot_function": "create_histogram",
        "required_fields": {"metric_value"},
    },
    "/charts/bar-category": {
        "plot_function": "create_bar_category_chart",
        "required_fields": {"category"},
    },
    "/charts/boxplot": {
        "plot_function": "create_boxplot",
        "required_fields": {"metric_value"},
    },
    "/charts/scatter": {
        "plot_function": "create_scatter_plot",
        "required_fields": {"metric_value", "secondary_metric"},
    },
    "/charts/grouped-comparison": {
        "plot_function": "create_grouped_comparison_chart",
        "required_fields": {"metric_value", "category"},
    },
}


def test_chart_endpoints_return_200_and_valid_image_paths():
    for endpoint in CHART_ENDPOINTS:
        response = client.get(endpoint)
        assert response.status_code == 200

        payload = response.json()
        assert isinstance(payload.get("image"), str)
        assert payload["image"].startswith("/static/plots/")


def test_chart_assets_are_saved_and_served_via_static_routes():
    static_root = Path(__file__).resolve().parents[1] / "static" / "plots"

    for endpoint in CHART_ENDPOINTS:
        response = client.get(endpoint)
        assert response.status_code == 200

        image_path = response.json()["image"]
        relative_file = image_path.replace("/static/plots/", "")
        disk_path = static_root / relative_file

        assert disk_path.exists()
        assert disk_path.stat().st_size > 0

        static_response = client.get(image_path)
        assert static_response.status_code == 200
        assert static_response.headers.get("content-type", "").startswith("image/")


def test_chart_endpoints_return_500_with_error_detail_on_plotting_failure(monkeypatch):
    expected_message = "forced plotting failure"

    for endpoint, metadata in CHART_ENDPOINTS.items():
        def _raise_plot_error(_df):
            raise RuntimeError(expected_message)

        monkeypatch.setattr(api_app_module, metadata["plot_function"], _raise_plot_error)

        response = client.get(endpoint)
        assert response.status_code == 500
        assert response.json().get("detail") == expected_message


def test_chart_endpoints_return_500_for_malformed_data(monkeypatch):
    malformed_df = pd.DataFrame([
        {"entity_id": "A", "unexpected": 1},
        {"entity_id": "B", "unexpected": 2},
    ])

    monkeypatch.setattr(api_app_module, "get_chart_dataframe", lambda: malformed_df)

    for endpoint in CHART_ENDPOINTS:
        response = client.get(endpoint)
        assert response.status_code == 500
        detail = str(response.json().get("detail", "")).lower()
        assert detail


def test_chart_data_fields_are_consistent_per_chart(monkeypatch):
    for endpoint, metadata in CHART_ENDPOINTS.items():
        def _assert_fields(df):
            assert metadata["required_fields"].issubset(set(df.columns))
            return "/static/plots/phase12_field_check.png"

        monkeypatch.setattr(api_app_module, metadata["plot_function"], _assert_fields)

        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.json()["image"] == "/static/plots/phase12_field_check.png"


def test_chart_generation_performance_and_image_size_are_reasonable():
    size_limit_bytes = 2 * 1024 * 1024

    for endpoint in CHART_ENDPOINTS:
        durations = []
        image_path = None

        for _ in range(2):
            start = time.perf_counter()
            response = client.get(endpoint)
            elapsed = time.perf_counter() - start
            durations.append(elapsed)

            assert response.status_code == 200
            image_path = response.json()["image"]

        assert max(durations) < 5.0

        image_name = image_path.split("/")[-1]
        disk_path = Path(__file__).resolve().parents[1] / "static" / "plots" / image_name
        assert disk_path.exists()
        assert disk_path.stat().st_size < size_limit_bytes
