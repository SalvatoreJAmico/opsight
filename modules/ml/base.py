from abc import ABC, abstractmethod
from typing import Any, List

from modules.ml.schemas import FeatureRecord


class BaseModel(ABC):
    @abstractmethod
    def fit(self, records: List[FeatureRecord]) -> None:
        pass

    @abstractmethod
    def predict(self, records: List[FeatureRecord]) -> List[Any]:
        pass

    @abstractmethod
    def evaluate(self, records: List[FeatureRecord]) -> dict:
        pass