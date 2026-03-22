from typing import List

from sklearn.ensemble import IsolationForest

from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord, PredictionRecord, PredictionResult


class IsolationForestModel(BaseModel):
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False

    def fit(self, records: List[FeatureRecord]) -> None:
        values = [[r.value] for r in records if r.value is not None]

        if not values:
            return

        self.model.fit(values)
        self.is_fitted = True

    def predict(self, records: List[FeatureRecord]) -> List[PredictionRecord]:
        if not self.is_fitted:
            self.fit(records)

        values = [[r.value] if r.value is not None else [0.0] for r in records]

        preds = self.model.predict(values)  # -1 = anomaly, 1 = normal
        scores = self.model.decision_function(values)

        results: List[PredictionRecord] = []

        for record, pred, score in zip(records, preds, scores):
            is_anomaly = pred == -1

            results.append(
                PredictionRecord(
                    entity_id=record.entity_id,
                    timestamp=record.timestamp,
                    value=record.value,
                    is_anomaly=is_anomaly,
                    anomaly_score=float(score),
                )
            )

        return results

    def evaluate(self, records: List[FeatureRecord]) -> PredictionResult:
        predictions = self.predict(records)
        anomaly_count = sum(1 for p in predictions if p.is_anomaly)

        return PredictionResult(
            total_records=len(predictions),
            anomaly_count=anomaly_count,
            records=predictions,
        )
   
