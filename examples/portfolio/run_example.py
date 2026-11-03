"""Offline synthetic demonstration of existing Opsight components, not the API pipeline."""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from modules.validation.validator import validate_canonical_record
from modules.persistence.local_storage import LocalStorage
from modules.ml.feature_pipeline import build_feature_dataset
from modules.ml.anomaly_zscore import ZScoreAnomalyModel


def run(output_dir):
    output_dir = Path(output_dir)
    # A fresh directory prevents silently overwriting an earlier result.
    output_dir.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).with_name('input.json')
    inputs = json.loads(fixture.read_text())
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    accepted, rejected = [], []
    for index, record in enumerate(inputs):
        result = validate_canonical_record(record)
        if result['status'] == 'valid':
            accepted.append(record)
        else:
            rejected.append({'record_index': index, 'record': record, 'errors': result['errors']})
    storage = LocalStorage(storage_path=str(output_dir / 'accepted.json'))
    storage.save_records(accepted)
    persisted = storage.load_records()
    if persisted != accepted:
        raise RuntimeError('JSON persistence round-trip failed')
    # Explicit example-specific mapping: canonical features.amount -> ML value.
    features = build_feature_dataset([
        {'entity_id': r['entity_id'], 'timestamp': r['timestamp'], 'value': r['features']['amount']}
        for r in persisted
    ])
    if features.invalid_records:
        raise RuntimeError('Example fixture contains invalid ML features')
    model = ZScoreAnomalyModel(threshold=2.0)
    model.fit(features.records)
    predictions = model.evaluate(features.records).model_dump()
    summary = {
        'run_started_utc': started,
        'python': platform.python_version(),
        'input_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'input_records': len(inputs), 'accepted_records': len(accepted),
        'rejected_records': len(rejected), 'persisted_records': len(persisted),
        'json_round_trip_equal': True,
        'anomaly_count': predictions['anomaly_count'],
        'anomaly_entity_ids': [r['entity_id'] for r in predictions['records'] if r['is_anomaly']],
        'model': 'ZScoreAnomalyModel', 'threshold': 2.0,
        'fit_mean': model.mean_value, 'fit_population_stddev': model.std_value,
        'component_elapsed_seconds': round(perf_counter() - timer, 6),
        'timing_scope': 'validation, JSON write/read, feature mapping, fit and predict; excludes imports and report writes',
        'limitations': 'Synthetic in-sample illustration. No labeled accuracy, throughput benchmark, API/UI, cloud ingestion or deployment verification.'
    }
    for name, value in [('rejected.json', rejected), ('anomalies.json', predictions), ('summary.json', summary)]:
        (output_dir / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory; must not already exist')
    print(json.dumps(run(parser.parse_args().output), indent=2))
