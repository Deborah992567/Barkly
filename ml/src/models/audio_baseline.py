from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import BaseEstimator, ClassifierMixin


class AudioBaselineModel(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = None,
        min_samples_split: int = 2,
        class_weight: str | dict | None = "balanced",
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.class_weight = class_weight
        self.random_state = random_state
        self.n_jobs = n_jobs
        self._model: RandomForestClassifier | None = None
        self._classes_: np.ndarray | None = None

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        class_weights: str | dict | None = None,
    ) -> "AudioBaselineModel":
        if class_weights is None:
            class_weights = self.class_weight
        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            class_weight=class_weights,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self._model.fit(X, y)
        self._classes_ = np.array(self._model.classes_)
        return self

    def fit(self, X: np.ndarray, y: np.ndarray) -> "AudioBaselineModel":
        return self.train(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self._model.predict_proba(X)

    @property
    def classes_(self) -> np.ndarray:
        return self._classes_

    @property
    def feature_importances_(self) -> np.ndarray:
        if self._model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self._model.feature_importances_

    @property
    def model(self) -> RandomForestClassifier | None:
        return self._model

    def save(self, path: str | Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "AudioBaselineModel":
        with open(path, "rb") as f:
            return pickle.load(f)