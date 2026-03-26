from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Any

import requests


@dataclass
class CheckResult:
    name: str
    success: bool
    detail: str
    data: dict[str, Any]


def _request_json(method: str, url: str, **kwargs: Any) -> requests.Response:
    response = requests.request(method=method, url=url, timeout=30, **kwargs)
    return response


def check_frontend_load(frontend_url: str) -> CheckResult:
    response = requests.get(frontend_url, timeout=30)
    content = response.text
    success = response.status_code == 200 and "<div id=\"root\"></div>" in content
    detail = "Frontend responded with expected SPA shell" if success else "Frontend did not return expected SPA shell"
    return CheckResult(
        name="frontend_load",
        success=success,
        detail=detail,
        data={"status_code": response.status_code, "content_length": len(content)},
    )


def check_api_health(api_base_url: str, frontend_url: str) -> CheckResult:
    response = _request_json(
        "GET",
        f"{api_base_url}/health",
        headers={"Origin": frontend_url},
    )
    payload = response.json()
    acao = response.headers.get("Access-Control-Allow-Origin")
    success = response.status_code == 200 and payload.get("status") == "ok"
    detail = "API health endpoint returned ok" if success else "API health endpoint failed"
    return CheckResult(
        name="api_health",
        success=success,
        detail=detail,
        data={
            "status_code": response.status_code,
            "payload": payload,
            "access_control_allow_origin": acao,
        },
    )


def check_pipeline_trigger(api_base_url: str, dataset_id: str = "sales_csv") -> CheckResult:
    response = _request_json(
        "POST",
        f"{api_base_url}/pipeline/trigger",
        json={"target": "cloud", "dataset_id": dataset_id},
        headers={"Content-Type": "application/json"},
    )
    payload = response.json()
    success = response.status_code == 200 and payload.get("status") == "processed"
    detail = "Pipeline trigger succeeded" if success else "Pipeline trigger failed"
    return CheckResult(
        name="pipeline_trigger",
        success=success,
        detail=detail,
        data={
            "status_code": response.status_code,
            "records_ingested": payload.get("records_ingested"),
            "records_valid": payload.get("records_valid"),
            "records_invalid": payload.get("records_invalid"),
            "records_persisted": payload.get("records_persisted"),
            "dataset_source_type": payload.get("dataset_source_type"),
            "dataset_path": payload.get("dataset_path"),
        },
    )


def check_charts_overview(api_base_url: str) -> CheckResult:
    response = _request_json("GET", f"{api_base_url}/charts/overview")
    payload = response.json()
    success = response.status_code == 200 and isinstance(payload.get("rows"), int)
    detail = "Charts overview returned dataset context" if success else "Charts overview check failed"
    return CheckResult(
        name="charts_overview",
        success=success,
        detail=detail,
        data={
            "status_code": response.status_code,
            "rows": payload.get("rows"),
            "source": payload.get("source"),
            "fields_count": len(payload.get("fields", [])) if isinstance(payload.get("fields"), list) else None,
        },
    )


def check_model_execution(api_base_url: str) -> CheckResult:
    response = _request_json("GET", f"{api_base_url}/ml/anomaly/kmeans")
    payload = response.json()
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    success = response.status_code == 200 and payload.get("status") == "completed"
    detail = "Model endpoint executed successfully" if success else "Model endpoint execution failed"
    return CheckResult(
        name="model_execution",
        success=success,
        detail=detail,
        data={
            "status_code": response.status_code,
            "anomalies": payload.get("anomalies"),
            "total": payload.get("total"),
            "summary_total_records": summary.get("total_records"),
        },
    )


def check_frontend_api_wiring(frontend_url: str, api_base_url: str) -> CheckResult:
    index_response = requests.get(frontend_url, timeout=30)
    index_html = index_response.text
    bundle_match = re.search(r"/assets/index-[^\"']+\.js", index_html)

    if not bundle_match:
        return CheckResult(
            name="frontend_api_wiring",
            success=False,
            detail="Unable to locate deployed frontend JS bundle path",
            data={"status_code": index_response.status_code},
        )

    bundle_path = bundle_match.group(0)
    bundle_response = requests.get(f"{frontend_url}{bundle_path}", timeout=30)
    bundle_content = bundle_response.text
    contains_api_url = api_base_url in bundle_content
    contains_dev_proxy = "/api-cloud" in bundle_content
    success = bundle_response.status_code == 200 and contains_api_url and not contains_dev_proxy
    detail = "Frontend bundle uses production API URL" if success else "Frontend bundle wiring is not production-safe"

    return CheckResult(
        name="frontend_api_wiring",
        success=success,
        detail=detail,
        data={
            "bundle_path": bundle_path,
            "bundle_status_code": bundle_response.status_code,
            "contains_api_url": contains_api_url,
            "contains_dev_proxy_route": contains_dev_proxy,
        },
    )


def run_smoke_suite(frontend_url: str, api_base_url: str, dataset_id: str) -> list[CheckResult]:
    checks = [
        check_frontend_load(frontend_url),
        check_api_health(api_base_url, frontend_url),
        check_pipeline_trigger(api_base_url, dataset_id=dataset_id),
        check_charts_overview(api_base_url),
        check_model_execution(api_base_url),
        check_frontend_api_wiring(frontend_url, api_base_url),
    ]
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live deployment smoke tests for Opsight UI and API.")
    parser.add_argument("--frontend-url", required=True, help="Public frontend URL.")
    parser.add_argument("--api-url", required=True, help="Public API base URL.")
    parser.add_argument("--dataset-id", default="sales_csv", help="Dataset id for pipeline trigger smoke test.")
    args = parser.parse_args()

    checks = run_smoke_suite(
        frontend_url=args.frontend_url.rstrip("/"),
        api_base_url=args.api_url.rstrip("/"),
        dataset_id=args.dataset_id,
    )
    passed = all(check.success for check in checks)

    report = {
        "passed": passed,
        "frontend_url": args.frontend_url,
        "api_url": args.api_url,
        "checks": [asdict(check) for check in checks],
    }

    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())