from statistics import mean, pstdev
from typing import List
import math

from sklearn.cluster import KMeans

from modules.ml.base import BaseModel
from modules.ml.schemas import FeatureRecord, PredictionRecord, PredictionResult


class KMeansAnomalyModel(BaseModel):
    """K-Means anomaly detector using distance to assigned centroid."""

    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.model: KMeans | None = None
        self.threshold: float = 0.0

    def fit(self, records: List[FeatureRecord]) -> None:
        values = [[r.value] if r.value is not None else [0.0] for r in records]

        if not values:
            self.model = None
            self.threshold = 0.0
            return

        cluster_count = max(1, min(self.n_clusters, len(values)))
        self.model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        labels = self.model.fit_predict(values)

        distances = [
            abs(point[0] - float(self.model.cluster_centers_[label][0]))
            for point, label in zip(values, labels)
        ]

        distance_mean = mean(distances) if distances else 0.0
        distance_std = pstdev(distances) if len(distances) > 1 else 0.0
        self.threshold = distance_mean + (2 * distance_std)

    def predict(self, records: List[FeatureRecord]) -> List[PredictionRecord]:
        if self.model is None:
            self.fit(records)

        if self.model is None:
            return []

        values = [[r.value] if r.value is not None else [0.0] for r in records]
        labels = self.model.predict(values)

        results: List[PredictionRecord] = []
        for record, point, label in zip(records, values, labels):
            distance = abs(point[0] - float(self.model.cluster_centers_[label][0]))
            is_anomaly = distance > self.threshold
            
            # Ensure distance is not NaN before storing
            distance_value = float(distance) if not (math.isnan(distance) or math.isinf(distance)) else None

            results.append(
                PredictionRecord(
                    entity_id=record.entity_id,
                    timestamp=record.timestamp,
                    value=record.value,
                    is_anomaly=is_anomaly,
                    anomaly_score=round(distance_value, 6) if distance_value is not None else None,
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