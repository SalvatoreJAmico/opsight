from statistics import mean, pstdev
from typing import List

from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord, PredictionRecord, PredictionResult


class ZScoreAnomalyModel(BaseModel):
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
        self.mean_value: float | None = None
        self.std_value: float | None = None

    def fit(self, records: List[FeatureRecord]) -> None:
        values = [r.value for r in records if r.value is not None]

        if not values:
            self.mean_value = 0.0
            self.std_value = 0.0
            return

        self.mean_value = mean(values)
        self.std_value = pstdev(values)

    def predict(self, records: List[FeatureRecord]) -> List[PredictionRecord]:
        if self.mean_value is None or self.std_value is None:
            self.fit(records)

        predictions: List[PredictionRecord] = []

        for record in records:
            is_anomaly = False
            z_score_value = None

            if record.value is not None and self.std_value not in (None, 0.0):
                z_score_value = abs((record.value - self.mean_value) / self.std_value)
                is_anomaly = z_score_value > self.threshold

            predictions.append(
                PredictionRecord(
                    entity_id=record.entity_id,
                    timestamp=record.timestamp,
                    value=record.value,
                    is_anomaly=is_anomaly,
                    anomaly_score=round(float(z_score_value), 4) if z_score_value is not None else None,
                )
            )

        return predictions

    def evaluate(self, records: List[FeatureRecord]) -> PredictionResult:
        predictions = self.predict(records)
        anomaly_count = sum(1 for p in predictions if p.is_anomaly)

        return PredictionResult(
            total_records=len(predictions),
            anomaly_count=anomaly_count,
            records=predictions,
        )