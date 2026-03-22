from typing import List, Optional
from pydantic import BaseModel


class FeatureRecord(BaseModel):
    entity_id: str
    timestamp: str
    value: Optional[float] = None
    label: Optional[int] = None


class DatasetBuildResult(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    records: List["FeatureRecord"]

class PredictionRecord(BaseModel):
    entity_id: str
    timestamp: str
    value: Optional[float]
    is_anomaly: bool
    anomaly_score: Optional[float] = None


class PredictionResult(BaseModel):
    total_records: int
    anomaly_count: int
    records: List["PredictionRecord"]