from typing import List
import math

import numpy as np
from sklearn.linear_model import LinearRegression

from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord, PredictionRecord, PredictionResult


class LinearRegressionModel(BaseModel):
    def __init__(self):
        self.model = LinearRegression()
        self.is_fitted = False

    def fit(self, records: List[FeatureRecord]) -> None:
        values = [r.value for r in records if r.value is not None]

        if len(values) < 2:
            return

        X = np.arange(len(values)).reshape(-1, 1)  # simple time index
        y = np.array(values)

        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, records: List[FeatureRecord], steps_ahead: int = 0) -> List[PredictionRecord]:
        if not self.is_fitted:
            self.fit(records)

        values = [r.value for r in records if r.value is not None]
        n = len(values)

        if n == 0:
            return []

        # include future steps
        total_points = n + steps_ahead
        X = np.arange(total_points).reshape(-1, 1)

        predictions = self.model.predict(X)

        results: List[PredictionRecord] = []

        for i in range(total_points):
            if i < n:
                record = records[i]
                entity_id = record.entity_id
                timestamp = record.timestamp
            else:
                entity_id = "future"
                timestamp = f"t+{i-n+1}"

            # Ensure prediction value is not NaN or Inf
            pred_value = predictions[i]
            if math.isnan(pred_value) or math.isinf(pred_value):
                pred_value = 0.0
            else:
                pred_value = round(float(pred_value), 4)

            results.append(
                PredictionRecord(
                    entity_id=entity_id,
                    timestamp=timestamp,
                    value=pred_value,
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