from typing import Any, List
from modules.ml.schemas import PredictionRecord, PredictionResult
from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord


class ThresholdAnomalyModel(BaseModel):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def fit(self, records: List[FeatureRecord]) -> None:
        # no training needed for fixed-threshold baseline
        return None

    def predict(self, records: List[FeatureRecord]) -> List[Any]:
        predictions = []

        for record in records:
            is_anomaly = False

            if record.value is not None and record.value > self.threshold:
                is_anomaly = True

            from modules.ml.schemas import PredictionRecord


            predictions.append(
                PredictionRecord(
                    entity_id=record.entity_id,
                    timestamp=record.timestamp,
                    value=record.value,
                    is_anomaly=is_anomaly,
                )
            )

        return predictions

    def evaluate(self, records: List[FeatureRecord]) -> dict:
        predictions = self.predict(records)

        total = len(predictions)
        anomalies = sum(1 for p in predictions if p.is_anomaly)

        return PredictionResult(
                total_records=total,
                anomaly_count=anomalies,
                records=predictions,
            )
    