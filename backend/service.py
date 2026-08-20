from __future__ import annotations

import logging
import threading
import time
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

try:
    from .models import improved_logistic, logistic, naive_bayes, svm
    from .utils.preprocessing import normalize_text
except ImportError:
    from models import improved_logistic, logistic, naive_bayes, svm
    from utils.preprocessing import normalize_text

logger = logging.getLogger("sentiment_analysis.models")

NAIVE_BAYES_NAME = "Naive Bayes"
LOGISTIC_REGRESSION_NAME = "Logistic Regression"
IMPROVED_LOGISTIC_NAME = "Improved Logistic Regression"
SVM_NAME = "SVM"
MODEL_NAMES = [
    NAIVE_BAYES_NAME,
    LOGISTIC_REGRESSION_NAME,
    IMPROVED_LOGISTIC_NAME,
    SVM_NAME,
]
STOPWORDS = {
    "the", "and", "this", "that", "with", "for", "was", "are", "but", "not",
    "have", "has", "had", "from", "they", "their", "you", "your", "its", "our",
    "very", "really", "just", "about", "into", "than", "then", "too", "can",
}


@dataclass
class ModelResult:
    name: str
    accuracy: float
    precision: float
    recall: float
    weighted_f1: float
    training_seconds: float
    labels: list[str]
    matrix: list[list[int]]
    report: dict[str, Any]
    samples: list[dict[str, str]]


def build_models() -> dict[str, Any]:
    return {
        NAIVE_BAYES_NAME: naive_bayes,
        LOGISTIC_REGRESSION_NAME: logistic,
        IMPROVED_LOGISTIC_NAME: improved_logistic,
        SVM_NAME: svm,
    }


def harmonize_labels(labels: pd.Series) -> pd.Series:
    mapping = {
        "pos": "positive", "positive": "positive", "4": "positive", "5": "positive",
        "neg": "negative", "negative": "negative", "0": "negative", "1": "negative",
        "neu": "neutral", "neutral": "neutral", "2": "neutral", "3": "neutral",
    }
    cleaned = labels.astype(str).str.strip().str.lower()
    return cleaned.map(lambda value: mapping.get(value, value))


def prepare_labels(series: pd.Series) -> tuple[pd.Series, str]:
    numeric = pd.to_numeric(series, errors="coerce")
    non_null_numeric = numeric.dropna()
    if not non_null_numeric.empty:
        unique_values = set(non_null_numeric.astype(float).unique().tolist())
        if unique_values.issubset({1.0, 2.0, 3.0, 4.0, 5.0}):
            mapped = numeric.map({
                1.0: "negative", 2.0: "negative", 3.0: "neutral",
                4.0: "positive", 5.0: "positive",
            })
            return mapped.fillna(""), (
                "Converted star ratings to sentiment: 1-2 negative, "
                "3 neutral, 4-5 positive."
            )
    return harmonize_labels(series), "Using labels as provided."


def infer_candidate_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    text_col = None
    label_col = None
    lowered = [(column, str(column).lower()) for column in df.columns]
    for token in ["reviewtext", "text", "content", "comment", "tweet", "message", "body", "review"]:
        text_col = next(
            (column for column, name in lowered if token in name and "reviewer" not in name),
            None,
        )
        if text_col is not None:
            break
    for token in ["sentiment", "label", "overall", "stars", "target", "class", "rating"]:
        label_col = next((column for column, name in lowered if token in name), None)
        if label_col is not None:
            break
    if text_col is None:
        candidates = [
            column for column in df.columns
            if df[column].dtype == "object"
            and df[column].astype(str).str.len().mean() > 25
        ]
        text_col = candidates[0] if candidates else None
    return text_col, label_col


def build_demo_product_dataset() -> pd.DataFrame:
    products = [
        "Bluetooth Speaker", "Phone Charger", "Laptop Sleeve", "Smart Watch",
        "Kitchen Blender", "Desk Lamp", "Gaming Mouse", "Travel Backpack",
    ]
    positive_starts = [
        "Absolutely love this", "Very impressed with this", "This is a reliable",
        "A genuinely excellent", "The quality of this", "Super happy with this",
    ]
    positive_features = [
        "battery life", "sound quality", "build quality", "comfort",
        "design", "performance", "packaging", "value",
    ]
    positive_endings = [
        "and it feels premium every day",
        "with smooth performance and zero issues",
        "and I would recommend it instantly",
        "because it works exactly as promised",
        "and the experience has been consistently great",
    ]
    negative_starts = [
        "Very disappointed with this", "This turned out to be a frustrating",
        "Sadly this is a poor", "I regret buying this", "The product became a terrible",
        "Such an unreliable",
    ]
    negative_features = [
        "battery", "screen", "material", "charging", "buttons", "fit", "motor", "performance",
    ]
    negative_endings = [
        "and it stopped working far too soon",
        "with constant problems and weak quality",
        "because the overall experience feels cheap",
        "and customer experience has been disappointing",
        "and it is not worth the price at all",
    ]
    neutral_starts = [
        "This is an average", "The product is a standard", "Overall it is a basic",
        "This feels like a normal", "The item is a fairly typical",
    ]
    neutral_features = [
        "design", "performance", "battery", "finish", "weight", "setup", "size", "packaging",
    ]
    neutral_endings = [
        "and it works about as expected",
        "with no major strengths or complaints",
        "and the results are acceptable for the price",
        "but it does not stand out in any way",
        "and the experience is fine for casual use",
    ]
    rows: list[dict[str, str]] = []
    for product in products:
        for start in positive_starts:
            for feature in positive_features[:4]:
                ending = positive_endings[(len(rows) + len(product)) % len(positive_endings)]
                rows.append({
                    "product": product,
                    "review": f"{start} {product.lower()} with excellent {feature} {ending}.",
                    "sentiment": "positive",
                })
        for start in negative_starts:
            for feature in negative_features[:4]:
                ending = negative_endings[(len(rows) + len(product)) % len(negative_endings)]
                rows.append({
                    "product": product,
                    "review": f"{start} {product.lower()} because the {feature} is weak {ending}.",
                    "sentiment": "negative",
                })
        for start in neutral_starts:
            for feature in neutral_features[:4]:
                ending = neutral_endings[(len(rows) + len(product)) % len(neutral_endings)]
                rows.append({
                    "product": product,
                    "review": f"{start} {product.lower()} with ordinary {feature} {ending}.",
                    "sentiment": "neutral",
                })
    return pd.DataFrame(rows)


def prepare_training_data(df: pd.DataFrame, text_col: str, label_col: str) -> pd.DataFrame:
    working = df[[text_col, label_col]].dropna().copy()
    working[text_col] = working[text_col].astype(str).str.strip()
    labels, _ = prepare_labels(working[label_col])
    working[label_col] = labels
    working = working[(working[text_col] != "") & (working[label_col] != "")]
    if working[label_col].nunique() < 2:
        raise ValueError("The label column must contain at least 2 classes.")
    if working[label_col].value_counts().min() < 2:
        raise ValueError("Each class should have at least 2 rows for a train/test split.")
    return working


def _probabilities(model: Any, text: str) -> dict[str, float] | None:
    classes = [str(value).lower() for value in getattr(model, "classes_", [])]
    if hasattr(model, "predict_proba"):
        values = np.asarray(model.predict_proba([text]))
        if values.ndim == 2 and values.shape[0] == 1:
            return {
                label: float(probability)
                for label, probability in zip(classes, values[0], strict=False)
            }
    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function([text]))
        if scores.ndim == 1:
            score = float(scores[0])
            probability = float(1 / (1 + np.exp(-score)))
            if len(classes) == 2:
                return {classes[0]: 1 - probability, classes[1]: probability}
            return {"confidence": float(1 / (1 + np.exp(-abs(score))))}
        if scores.ndim == 2 and scores.shape[0] == 1:
            shifted = scores[0] - np.max(scores[0])
            values = np.exp(shifted) / np.exp(shifted).sum()
            return {
                label: float(probability)
                for label, probability in zip(classes, values, strict=False)
            }
    return None


def top_words(
    df: pd.DataFrame,
    text_col: str,
    label_col: str,
    label: str,
    top_n: int,
) -> list[dict[str, Any]]:
    labels, _ = prepare_labels(df[label_col])
    words: list[str] = []
    for text in df.loc[labels == label, text_col].dropna().astype(str):
        words.extend(
            token for token in normalize_text(text).split()
            if len(token) > 2 and token not in STOPWORDS
        )
    return [
        {"word": word, "count": count}
        for word, count in Counter(words).most_common(top_n)
    ]


class ModelRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._models: dict[str, Any] = {}
        self._results: list[ModelResult] = []
        self._dataset = build_demo_product_dataset()
        self._text_col = "review"
        self._label_col = "sentiment"
        self._test_size = 0.2
        self._random_state = 42

    @property
    def ready(self) -> bool:
        return bool(self._models)

    @property
    def loaded_model_names(self) -> list[str]:
        return [name for name in MODEL_NAMES if name in self._models]

    def has_model(self, model_name: str) -> bool:
        return model_name in self._models

    def ensure_ready(self) -> None:
        if self.ready:
            logger.debug("Model registry already initialized")
            return
        with self._lock:
            if not self.ready:
                logger.info("Initializing %d model pipelines from the bundled dataset", len(MODEL_NAMES))
                try:
                    self.train(
                        self._dataset,
                        self._text_col,
                        self._label_col,
                        MODEL_NAMES,
                        0.2,
                        42,
                    )
                except Exception:
                    logger.exception("Model initialization failed")
                    raise

    def ensure_model_ready(self, model_name: str) -> Any:
        """Return a model, rebuilding only that pipeline if training excluded it."""
        if model_name not in MODEL_NAMES:
            raise ValueError(f"Unknown model selection: {model_name}")
        model = self._models.get(model_name)
        if model is not None:
            return model
        with self._lock:
            model = self._models.get(model_name)
            if model is not None:
                return model
            logger.info(
                "Restoring missing runtime model: %s (rows=%d)",
                model_name,
                len(self._dataset),
            )
            working = prepare_training_data(
                self._dataset,
                self._text_col,
                self._label_col,
            )
            X_train, _, y_train, _ = train_test_split(
                working[self._text_col],
                working[self._label_col],
                test_size=self._test_size,
                random_state=self._random_state,
                stratify=working[self._label_col],
            )
            model = build_models()[model_name].train(X_train, y_train)
            self._models[model_name] = model
            logger.info("Runtime model restored: %s", model_name)
            return model

    def train(
        self,
        df: pd.DataFrame,
        text_col: str,
        label_col: str,
        selected_models: list[str],
        test_size: float,
        random_state: int,
    ) -> dict[str, Any]:
        working = prepare_training_data(df, text_col, label_col)
        logger.info(
            "Training requested: rows=%d models=%s test_size=%.2f random_state=%d",
            len(working),
            ", ".join(selected_models),
            test_size,
            random_state,
        )
        unknown = [name for name in selected_models if name not in MODEL_NAMES]
        if unknown:
            raise ValueError(f"Unknown model selection: {', '.join(unknown)}")
        X_train, X_test, y_train, y_test = train_test_split(
            working[text_col],
            working[label_col],
            test_size=test_size,
            random_state=random_state,
            stratify=working[label_col],
        )
        models: dict[str, Any] = {}
        results: list[ModelResult] = []
        modules = build_models()
        for model_name in selected_models:
            logger.info("Loading and training model: %s", model_name)
            started = time.perf_counter()
            model = modules[model_name].train(X_train, y_train)
            elapsed = time.perf_counter() - started
            logger.info("Model ready: %s (%.3fs)", model_name, elapsed)
            predictions = np.asarray(modules[model_name].predict(model, X_test))
            labels = sorted(pd.Series(y_test).astype(str).unique().tolist())
            matrix = confusion_matrix(y_test, predictions, labels=labels)
            report = classification_report(
                y_test, predictions, output_dict=True, zero_division=0
            )
            samples = [
                {"actual": str(actual), "predicted": str(predicted)}
                for actual, predicted in zip(y_test.head(20), predictions[:20], strict=False)
            ]
            results.append(ModelResult(
                name=model_name,
                accuracy=float(accuracy_score(y_test, predictions)),
                precision=float(precision_score(
                    y_test, predictions, average="weighted", zero_division=0
                )),
                recall=float(recall_score(
                    y_test, predictions, average="weighted", zero_division=0
                )),
                weighted_f1=float(f1_score(y_test, predictions, average="weighted")),
                training_seconds=float(elapsed),
                labels=labels,
                matrix=matrix.astype(int).tolist(),
                report=report,
                samples=samples,
            ))
            models[model_name] = model
        self._models = models
        self._results = results
        self._dataset = df.copy()
        self._text_col = text_col
        self._label_col = label_col
        self._test_size = test_size
        self._random_state = random_state
        logger.info("Training completed; %d models are ready", len(models))
        return self.training_payload(df, text_col, label_col, ensure=False)

    def predict(self, text: str, model_name: str) -> dict[str, Any]:
        logger.info(
            "Running prediction: model=%s characters=%d",
            model_name,
            len(str(text)),
        )
        model = self.ensure_model_ready(model_name)
        started = time.perf_counter()
        sentiment = str(build_models()[model_name].predict(model, [str(text)])[0]).lower()
        probabilities = _probabilities(model, str(text))
        elapsed_ms = (time.perf_counter() - started) * 1000
        confidence = probabilities.get(sentiment) if probabilities else None
        if confidence is None and probabilities and "confidence" in probabilities:
            confidence = probabilities["confidence"]
        logger.info("Prediction result: model=%s sentiment=%s", model_name, sentiment)
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "probability": confidence,
            "probabilities": probabilities,
            "inference_time_ms": elapsed_ms,
            "model_used": model_name,
        }

    def training_payload(
        self,
        df: pd.DataFrame | None = None,
        text_col: str | None = None,
        label_col: str | None = None,
        ensure: bool = True,
    ) -> dict[str, Any]:
        if ensure:
            self.ensure_ready()
        dataset = self._dataset if df is None else df
        text_column = self._text_col if text_col is None else text_col
        label_column = self._label_col if label_col is None else label_col
        prepared, note = prepare_labels(dataset[label_column])
        counts = prepared.value_counts().sort_index()
        best = max(self._results, key=lambda item: (item.accuracy, item.weighted_f1))
        return {
            "dataset": {
                "name": "Bundled product reviews",
                "rows": int(len(dataset)),
                "columns": int(len(dataset.columns)),
                "classes": int(counts.size),
                "missing_values": int(dataset.isna().sum().sum()),
                "text_column": text_column,
                "label_column": label_column,
                "label_note": note,
                "distribution": [
                    {"sentiment": str(label), "count": int(count)}
                    for label, count in counts.items()
                ],
            },
            "leaderboard": [
                {
                    "model": result.name,
                    "accuracy": result.accuracy,
                    "precision": result.precision,
                    "recall": result.recall,
                    "weighted_f1": result.weighted_f1,
                    "training_seconds": result.training_seconds,
                }
                for result in sorted(
                    self._results,
                    key=lambda item: (item.accuracy, item.weighted_f1),
                    reverse=True,
                )
            ],
            "evaluation": [
                {
                    "model": result.name,
                    "labels": result.labels,
                    "confusion_matrix": result.matrix,
                    "classification_report": result.report,
                    "samples": result.samples,
                }
                for result in self._results
            ],
            "word_clouds": {
                label: top_words(dataset, text_column, label_column, label, 24)
                for label in ["positive", "negative", "neutral"]
            },
            "best_model": best.name,
        }

    def business_insights(self) -> dict[str, Any]:
        self.ensure_ready()
        labels, _ = prepare_labels(self._dataset[self._label_col])
        counts = labels.value_counts()
        distribution = [
            {"sentiment": label, "count": int(counts.get(label, 0))}
            for label in ["positive", "negative", "neutral"]
        ]
        positive = top_words(
            self._dataset, self._text_col, self._label_col, "positive", 10
        )
        negative = top_words(
            self._dataset, self._text_col, self._label_col, "negative", 10
        )
        positive_terms = ", ".join(item["word"] for item in positive[:3])
        negative_terms = ", ".join(item["word"] for item in negative[:3])
        summary = (
            f"Most negative feedback is related to {negative_terms}, while positive "
            f"reviews frequently mention {positive_terms}."
        )
        return {
            "distribution": distribution,
            "positive_keywords": positive,
            "negative_keywords": negative,
            "summary": summary,
        }

    def load_uploaded_dataset(self, filename: str, content: bytes) -> pd.DataFrame:
        suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        source = BytesIO(content)
        try:
            if suffix == "csv":
                return pd.read_csv(source)
            if suffix == "json":
                return pd.read_json(source)
            if suffix in {"xlsx", "xls"}:
                return pd.read_excel(source)
            raise ValueError("Unsupported file format. Upload CSV, JSON, XLSX, or XLS.")
        except ValueError:
            raise
        except Exception as exc:
            format_name = suffix.upper() or "UNKNOWN"
            raise ValueError(
                f"Could not parse the uploaded {format_name} dataset: {exc}"
            ) from exc


registry = ModelRegistry()
