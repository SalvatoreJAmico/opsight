from typing import List
import math

from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord, PredictionRecord, PredictionResult


class MovingAverageModel(BaseModel):
    def __init__(self, window_size: int = 2):
        self.window_size = window_size

    def fit(self, records: List[FeatureRecord]) -> None:
        # no training needed
        return None

    def predict(self, records: List[FeatureRecord], steps_ahead: int = 0) -> List[PredictionRecord]:
        values = [r.value for r in records if r.value is not None]

        if not values:
            return []

        results: List[PredictionRecord] = []

        # existing points (just return original values)
        for r in records:
            results.append(
                PredictionRecord(
                    entity_id=r.entity_id,
                    timestamp=r.timestamp,
                    value=r.value,
                    is_anomaly=False,
                    anomaly_score=None,
                )
            )

        # future predictions
        history = values.copy()

        for i in range(steps_ahead):
            window = history[-self.window_size:]
            avg = sum(window) / len(window)

            # Ensure average is not NaN or Inf
            if math.isnan(avg) or math.isinf(avg):
                avg = 0.0
            else:
                avg = round(avg, 4)

            history.append(avg)

            results.append(
                PredictionRecord(
                    entity_id="future",
                    timestamp=f"t+{i+1}",
                    value=avg,
                    is_anomaly=False,
                    anomaly_score=None,
                )
            )

        return results

    def evaluate(self, records: List[FeatureRecord]) -> PredictionResult:
        preds = self.predict(records)

        return PredictionResult(
            total_records=len(preds),
            anomaly_count=0,
            records=preds,
        )