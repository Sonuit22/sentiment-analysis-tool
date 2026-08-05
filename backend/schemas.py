from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ModelName = Literal[
    "Naive Bayes",
    "Logistic Regression",
    "Improved Logistic Regression",
    "SVM",
]


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    model: ModelName = "Improved Logistic Regression"


class PredictResponse(BaseModel):
    sentiment: str
    confidence: float | None
    probability: float | None
    probabilities: dict[str, float] | None
    inference_time_ms: float
    model_used: str


class HealthResponse(BaseModel):
    status: str
    service: str
    models_ready: bool
    available_models: list[str]
    version: str
