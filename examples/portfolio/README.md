# Opsight: a reproducible validation-to-anomaly example

This small, offline example exercises existing Opsight components with **synthetic data**. It does not call the live demo, API, Azure, or any external service. It is a component walkthrough, not a run of `run_pipeline.py`.

## Reproduce

From the repository root, use Python 3.12 with the repository dependencies installed in a virtual environment:

```sh
python -m pip install -r requirements.txt
python examples/portfolio/run_example.py --output /tmp/opsight-portfolio-run
python -m unittest tests.test_portfolio_example tests.test_validation -v
```

Windows users can replace `/tmp/opsight-portfolio-run` with an unused local path. The output directory must not already exist: the example deliberately refuses to overwrite earlier results. It uses a separate explicit storage path, not production environment settings. No credentials are needed.

## Input and processing

[`input.json`](input.json) contains 14 canonical records. Eleven have numeric `features.amount` values: `10, 11, 9, 10, 12, 8, 11, 9, 10, 10, 100`. Three deliberately malformed records omit an entity ID, omit a timestamp, or supply a list where the features dictionary belongs.

1. The repository's `validate_canonical_record` checks each record. The example records rejected input and the actual validation errors.
2. The repository's `LocalStorage` writes accepted records as JSON, reads them back, and the example checks exact equality.
3. An explicit mapping in this example projects `features.amount` to the ML layer's `value` field. This is example-specific glue, not a claim that every dataset has this field.
4. The repository's `build_feature_dataset` and `ZScoreAnomalyModel` fit and score the accepted records at threshold 2.0. A record is flagged when its absolute Z-score exceeds that threshold.

## Observed result, November 3, 2026

See the actual saved [`summary.json`](evidence/summary.json), [`accepted.json`](evidence/accepted.json), [`rejected.json`](evidence/rejected.json), and [`anomalies.json`](evidence/anomalies.json).

| Stage | Observed result |
| --- | --- |
| Input | 14 synthetic records |
| Validation | 11 accepted; 3 rejected with explicit reasons |
| Persistence | 11 JSON records read back equal to accepted input |
| Anomaly output | 1 flag: `synthetic-011`, amount 100, absolute Z-score 3.1597 |

The full backend suite passed locally: **148 tests passed, 5 warnings, 8.18 seconds** (`python -m pytest -q`). Warnings included FastAPI startup-event deprecation and physical CPU-core detection. Frontend tests and live deployment checks were not run. See [environment details](evidence/environment.json).

The baseline source is commit `23ba93560868f40218f5af4e5d520c2d4151aff4` on `opsight_2.0`. The first recorded run used Python 3.12.14. It measured 0.001451 seconds for validation, JSON write/read, feature mapping, fit and predict on this tiny fixture; imports and report writes are excluded. **This single local timing is not a throughput, latency, or scalability benchmark.** Machine load and runtime versions will change timing.

## What this does and does not establish

- Demonstrates an inspectable path from structural validation through local persistence to a model result using existing repository code.
- Three regression checks cover functional results, refusal to overwrite prior output, and deterministic data outputs across repeated runs. Dates and timings intentionally vary.
- The current structural validator checks presence and the features container type. This example does not establish exhaustive type, timestamp, range, duplicate, or semantic validation.
- The deliberately large value is scored on the same synthetic dataset used for fitting. There is no labeled holdout evaluation, so this is **not evidence of anomaly-detection accuracy or production usefulness**.
- It does not test CSV ingestion, the full orchestration runner, Parquet, cloud storage, API, UI, concurrent use, or live deployment health.
- This walkthrough and its tests were prepared with AI assistance. Their existence does not by itself demonstrate independent implementation proficiency.

For the deployed demo: if the interface shows “Checking API...”, wait for the connection result before running a dataset. The live demo is separate from this saved example; these files remain readable without a live API.
