from __future__ import annotations

import base64
import importlib
import html
import json
import random
import re
import tempfile
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st  # type: ignore[import]
import streamlit.components.v1 as components
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from backend.models import improved_logistic, logistic, naive_bayes, svm
from backend.utils.preprocessing import normalize_text

APP_CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(34, 197, 94, 0.14), transparent 30%),
        radial-gradient(circle at top right, rgba(56, 189, 248, 0.12), transparent 24%),
        linear-gradient(180deg, #08111f 0%, #0f172a 100%);
    color: #e5edf7;
}
.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 3rem;
    max-width: 1220px;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
}
[data-testid="stHeader"] {
    background: rgba(8, 17, 31, 0.82) !important;
    border-bottom: 1px solid rgba(71, 85, 105, 0.32) !important;
    backdrop-filter: blur(10px);
}
[data-testid="stToolbar"] {
    right: 1rem !important;
}
.hero {
    padding: 1.65rem 1.8rem;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(18, 52, 86, 0.94) 55%, rgba(14, 116, 144, 0.92) 100%);
    color: #f8fafc;
    box-shadow: 0 24px 55px rgba(2, 8, 23, 0.42);
    border: 1px solid rgba(148, 163, 184, 0.16);
    margin-bottom: 1.35rem;
}
.hero-brand-row {
    display: flex;
    align-items: center;
    margin-bottom: 1.15rem;
}
.brand-plate {
    display: inline-flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 18px;
    background: rgba(2, 6, 23, 0.36);
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 16px 34px rgba(2, 8, 23, 0.24);
}
.brand-logo-side {
    width: 88px;
    height: 88px;
    border-radius: 16px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.08);
    flex-shrink: 0;
    border: 1px solid rgba(255, 255, 255, 0.12);
}
.brand-logo-side img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}
.brand-name-side {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    min-width: 0;
}
.brand-chip {
    padding: 0.4rem 0.72rem;
    border-radius: 999px;
    background: rgba(56, 189, 248, 0.16);
    color: #7dd3fc;
    font-size: 0.74rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 700;
}
.brand-typing-shell {
    display: inline-flex;
    align-items: center;
    min-width: 8ch;
    border-right: 2px solid rgba(125, 211, 252, 0.95);
    padding-right: 0.12rem;
    overflow: hidden;
}
.brand-typing {
    display: inline-block;
    width: 0;
    overflow: hidden;
    white-space: nowrap;
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    font-family: "Consolas", "Courier New", monospace;
    text-transform: lowercase;
    color: #f8fafc;
    animation: brandTyping 4.2s steps(7, end) infinite;
}
@keyframes brandTyping {
    0%, 12% { width: 0; }
    30%, 72% { width: 7.8ch; }
    100% { width: 0; }
}
@keyframes brandCaret {
    0%, 49% { border-color: rgba(125, 211, 252, 0.95); }
    50%, 100% { border-color: transparent; }
}
.brand-typing-shell {
    animation: brandCaret 0.9s step-end infinite;
}
@media (max-width: 760px) {
    .brand-plate {
        width: 100%;
        justify-content: flex-start;
        flex-wrap: wrap;
    }
    .brand-logo-side {
        width: 72px;
        height: 72px;
    }
    .brand-name-side {
        width: 100%;
        gap: 0.7rem;
    }
    .brand-typing {
        font-size: 1.05rem;
    }
}
.hero h1 {
    margin: 0 0 0.35rem 0;
    font-size: 2.4rem;
    letter-spacing: -0.03em;
}
.hero-title {
    margin: 0 0 0.45rem 0;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.03em;
    color: #f8fafc;
}
.hero-copy {
    margin: 0;
    font-size: 1rem;
    line-height: 1.65;
    max-width: 60rem;
    color: #dbe7f5;
}
.hero p {
    margin: 0;
    font-size: 1rem;
    line-height: 1.65;
    max-width: 60rem;
}
.cloud-wrap {
    min-height: 340px;
    padding: 1rem;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.96) 0%, rgba(17, 24, 39, 0.96) 100%);
    border: 1px solid rgba(71, 85, 105, 0.55);
    position: relative;
    overflow: hidden;
}
.cloud-word {
    display: inline-block;
    margin: 0.35rem 0.55rem;
    line-height: 1.1;
    font-weight: 700;
}
.metric-note {
    font-size: 0.92rem;
    color: #94a3b8;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%) !important;
}
[data-testid="stSidebar"] > div {
    background: transparent !important;
}
[data-testid="stSidebarNav"] {
    padding-top: 1rem !important;
}
[data-testid="stSidebarNavItems"] {
    padding-top: 0.5rem !important;
}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #f8fafc !important;
}
.stMarkdown,
.stCaption,
.stSubheader,
.stHeader,
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stNumberInput label,
.stDateInput label,
.stTimeInput label,
.stFileUploader label,
h1, h2, h3, h4, h5, h6, p, li, span {
    color: #e5edf7 !important;
}
.stCaption {
    color: #94a3b8 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.72) !important;
    border: 1px solid rgba(71, 85, 105, 0.38) !important;
    border-radius: 18px !important;
    box-shadow: 0 18px 40px rgba(2, 8, 23, 0.18);
}
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(71, 85, 105, 0.36);
    border-radius: 16px;
    padding: 0.8rem 1rem;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #f8fafc !important;
}
[data-testid="stMetricDelta"] {
    color: #38bdf8 !important;
}
.stTextInput input,
.stTextArea textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stNumberInput"] input {
    background: #0f172a !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    caret-color: #38bdf8 !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {
    background: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid #475569 !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
[data-testid="stNumberInput"] input::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stNumberInput"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 1px #38bdf8 !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] *,
[data-testid="stMultiSelect"] div[data-baseweb="select"] * {
    color: #f8fafc !important;
}
div[role="listbox"] {
    background: #0f172a !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
}
div[role="option"] {
    background: #0f172a !important;
    color: #f8fafc !important;
}
div[role="option"]:hover {
    background: #1e293b !important;
}
.stButton > button {
    background: linear-gradient(135deg, #0f766e 0%, #0f4c81 100%) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0f8a81 0%, #16629c 100%) !important;
    border-color: #38bdf8 !important;
    color: #f8fafc !important;
}
[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {
    background: #38bdf8 !important;
    border-color: #38bdf8 !important;
}
[data-testid="stSidebar"] [data-baseweb="slider"] > div > div {
    color: #f8fafc !important;
}
[data-baseweb="tab-list"] {
    gap: 0.35rem;
}
[data-baseweb="tab"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 999px !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(71, 85, 105, 0.24) !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.92), rgba(15, 76, 129, 0.92)) !important;
    color: #f8fafc !important;
}
.stDataFrame, .stTable {
    border-radius: 16px !important;
    overflow: hidden;
}
</style>
"""


LABEL_COLORS = {
    "negative": "#c44536",
    "neutral": "#d88c1f",
    "positive": "#2d936c",
}


STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "have", "from", "they", "were",
    "been", "would", "there", "their", "about", "your", "very", "just", "really",
    "into", "than", "when", "while", "after", "before", "because", "been", "being",
    "product", "amazon", "flipkart", "item", "purchase", "bought", "using", "used",
}

NAIVE_BAYES_NAME = "Naive Bayes"
LOGISTIC_REGRESSION_NAME = "Logistic Regression"
IMPROVED_LOGISTIC_NAME = "Improved Logistic Regression"
SVM_NAME = "SVM"
BUNDLED_DATASET_LABEL = "Bundled product reviews"
PROJECT_ROOT = Path(__file__).resolve().parent
BRAND_HEADER_IMAGE_PATH = PROJECT_ROOT / "images" / "ib_brand_icon.png"
BRAND_PAGE_ICON_PATH = PROJECT_ROOT / "images" / "ib_brand_icon_square.png"


@dataclass
class ModelResult:
    name: str
    accuracy: float
    precision: float
    recall: float
    weighted_f1: float
    training_seconds: float
    y_true: pd.Series
    y_pred: np.ndarray
    report: pd.DataFrame


@dataclass
class ExperimentArtifacts:
    results: list[ModelResult]
    trained_models: dict[str, object]


@lru_cache(maxsize=1)
def get_brand_image_data_uri() -> str | None:
    if not BRAND_HEADER_IMAGE_PATH.exists():
        return None
    encoded = base64.b64encode(BRAND_HEADER_IMAGE_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@lru_cache(maxsize=1)
def get_brand_page_icon():
    icon_path = BRAND_PAGE_ICON_PATH if BRAND_PAGE_ICON_PATH.exists() else BRAND_HEADER_IMAGE_PATH
    if not icon_path.exists():
        return "SA"
    with Image.open(icon_path) as brand_image:
        return brand_image.copy()


def configure_page(page_title: str):
    st.set_page_config(page_title=page_title, page_icon=get_brand_page_icon(), layout="wide")


def apply_global_styles():
    st.markdown(APP_CSS, unsafe_allow_html=True)
    components.html(
        """
        <script>
        const root = window.parent.document;
        const appView = root.querySelector('[data-testid="stAppViewContainer"]');
        const main = root.querySelector('[data-testid="stAppViewContainer"] section.main');
        const block = root.querySelector('.main .block-container');

        if (appView) {
            appView.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        }
        if (main) {
            main.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        }
        if (block) {
            block.scrollIntoView({ block: 'start', inline: 'nearest' });
        }
        </script>
        """,
        height=0,
    )


def infer_candidate_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    text_col = None
    label_col = None
    text_priority = [
        "reviewtext", "text", "content", "comment", "tweet", "message", "body", "review",
    ]
    label_priority = [
        "sentiment", "label", "overall", "stars", "target", "class", "rating",
    ]

    lowered_columns = [(col, col.lower()) for col in df.columns]

    for token in text_priority:
        for col, lowered in lowered_columns:
            if token in lowered and "reviewer" not in lowered:
                text_col = col
                break
        if text_col is not None:
            break

    for token in label_priority:
        for col, lowered in lowered_columns:
            if token in lowered:
                label_col = col
                break
        if label_col is not None:
            break

    if text_col is None:
        text_candidates = [
            col for col in df.columns
            if df[col].dtype == "object" and df[col].astype(str).str.len().mean() > 25
        ]
        text_col = text_candidates[0] if text_candidates else None

    if label_col is None:
        label_candidates = []
        for col in df.columns:
            prepared_labels, _ = prepare_labels(df[col])
            counts = prepared_labels[prepared_labels != ""].value_counts()
            if 2 <= len(counts) <= 5 and counts.min() >= 2:
                label_candidates.append(col)
        label_col = label_candidates[0] if label_candidates else None

    return text_col, label_col


def read_dataset(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix == ".json":
        return pd.read_json(uploaded_file)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file format. Please upload CSV, JSON, or Excel.")


def harmonize_labels(labels: pd.Series) -> pd.Series:
    mapping = {
        "pos": "positive",
        "positive": "positive",
        "4": "positive",
        "5": "positive",
        "neg": "negative",
        "negative": "negative",
        "0": "negative",
        "1": "negative",
        "neu": "neutral",
        "neutral": "neutral",
        "2": "neutral",
        "3": "neutral",
    }
    cleaned = labels.astype(str).str.strip().str.lower()
    return cleaned.map(lambda value: mapping.get(value, value))


def prepare_labels(series: pd.Series) -> tuple[pd.Series, str]:
    numeric = pd.to_numeric(series, errors="coerce")
    non_null_numeric = numeric.dropna()
    if not non_null_numeric.empty:
        unique_values = set(non_null_numeric.astype(float).unique().tolist())
        if unique_values.issubset({1.0, 2.0, 3.0, 4.0, 5.0}):
            mapped = numeric.map(
                {
                    1.0: "negative",
                    2.0: "negative",
                    3.0: "neutral",
                    4.0: "positive",
                    5.0: "positive",
                }
            )
            return mapped.fillna(""), "Converted star ratings to sentiment: 1-2 negative, 3 neutral, 4-5 positive."
    return harmonize_labels(series), "Using labels as provided."


def build_models():
    return {
        NAIVE_BAYES_NAME: naive_bayes,
        LOGISTIC_REGRESSION_NAME: logistic,
        IMPROVED_LOGISTIC_NAME: improved_logistic,
        SVM_NAME: svm,
    }


def get_model_options() -> list[str]:
    return list(build_models().keys())


def prepare_training_data(df: pd.DataFrame, text_col: str, label_col: str) -> pd.DataFrame:
    working = df[[text_col, label_col]].dropna().copy()
    working[text_col] = working[text_col].astype(str).str.strip()
    prepared_labels, _ = prepare_labels(working[label_col])
    working[label_col] = prepared_labels
    working = working[(working[text_col] != "") & (working[label_col] != "")]

    if working[label_col].nunique() < 2:
        raise ValueError("The label column must contain at least 2 classes.")

    if working[label_col].value_counts().min() < 2:
        raise ValueError("Each class should have at least 2 rows for a train/test split.")

    return working


def train_selected_models(
    df: pd.DataFrame,
    text_col: str,
    label_col: str,
    selected_models: list[str],
    test_size: float,
    random_state: int,
) -> ExperimentArtifacts:
    working = prepare_training_data(df, text_col, label_col)

    X_train, X_test, y_train, y_test = train_test_split(
        working[text_col],
        working[label_col],
        test_size=test_size,
        random_state=random_state,
        stratify=working[label_col],
    )

    results = []
    trained_models: dict[str, object] = {}
    model_modules = build_models()

    for model_name in selected_models:
        model_module = model_modules[model_name]
        train_start = time.perf_counter()
        model = model_module.train(X_train, y_train)
        training_seconds = time.perf_counter() - train_start
        preds = np.array(model_module.predict(model, X_test))
        trained_models[model_name] = model
        report = pd.DataFrame(
            classification_report(y_test, preds, output_dict=True, zero_division=0)
        ).transpose()
        results.append(
            ModelResult(
                name=model_name,
                accuracy=accuracy_score(y_test, preds),
                precision=precision_score(y_test, preds, average="weighted", zero_division=0),
                recall=recall_score(y_test, preds, average="weighted", zero_division=0),
                weighted_f1=f1_score(y_test, preds, average="weighted"),
                training_seconds=training_seconds,
                y_true=y_test.reset_index(drop=True),
                y_pred=preds,
                report=report,
            )
        )

    return ExperimentArtifacts(results=results, trained_models=trained_models)


def get_experiment_signature(
    dataset_name: str,
    text_col: str,
    label_col: str,
    selected_models: list[str],
    test_size: float,
    random_state: int,
    row_count: int,
) -> tuple:
    return (
        dataset_name,
        text_col,
        label_col,
        tuple(selected_models),
        float(test_size),
        int(random_state),
        int(row_count),
    )


def run_experiment(
    df: pd.DataFrame,
    text_col: str,
    label_col: str,
    selected_models: list[str],
    test_size: float,
    random_state: int,
) -> list[ModelResult]:
    return train_selected_models(
        df=df,
        text_col=text_col,
        label_col=label_col,
        selected_models=selected_models,
        test_size=test_size,
        random_state=random_state,
    ).results


def plot_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, title: str):
    labels = sorted(pd.Series(y_true).astype(str).unique().tolist())
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    image = ax.imshow(matrix, cmap="YlOrBr")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15)
    ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, matrix[i, j], ha="center", va="center", color="#2d2a26", fontsize=11, fontweight="bold")
    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    fig.tight_layout()
    return fig


def plot_distribution(series: pd.Series, title: str):
    counts = prepare_labels(series)[0].value_counts().sort_index()
    colors = [LABEL_COLORS.get(label, "#4c78a8") for label in counts.index]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(counts.index, counts.values, color=colors, width=0.6)
    ax.set_title(title)
    ax.set_ylabel("Count")
    ax.grid(axis="y", alpha=0.18)
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{int(bar.get_height())}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    fig.tight_layout()
    return fig


def plot_model_comparison(results: list[ModelResult]):
    df = pd.DataFrame(
        {
            "Model": [result.name for result in results],
            "Accuracy": [result.accuracy for result in results],
            "Weighted F1": [result.weighted_f1 for result in results],
        }
    )
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(df))
    width = 0.34
    acc_bars = ax.bar(x - width / 2, df["Accuracy"], width=width, color="#2d936c", label="Accuracy")
    f1_bars = ax.bar(x + width / 2, df["Weighted F1"], width=width, color="#1f4e5f", label="Weighted F1")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Model"], rotation=12, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison")
    ax.legend()
    for bars in (acc_bars, f1_bars):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{bar.get_height():.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    return fig


def top_words_by_label(df: pd.DataFrame, text_col: str, label_col: str, label: str) -> pd.Series:
    prepared_labels, _ = prepare_labels(df[label_col])
    subset = df[prepared_labels == label][text_col].dropna().astype(str)
    tokens: list[str] = []
    for text in subset:
        tokens.extend(
            token for token in normalize_text(text).split()
            if len(token) > 2 and token not in STOPWORDS
        )
    if not tokens:
        return pd.Series(dtype=int)
    return pd.Series(tokens).value_counts().head(24)


def get_cleaned_text_by_label(df: pd.DataFrame, text_col: str, label_col: str, label: str) -> pd.Series:
    prepared_labels, _ = prepare_labels(df[label_col])
    subset = df.loc[prepared_labels == label, text_col].dropna().astype(str)
    return subset.map(normalize_text)


def get_binary_sentiment_counts(df: pd.DataFrame, label_col: str) -> pd.Series:
    prepared_labels, _ = prepare_labels(df[label_col])
    counts = prepared_labels.value_counts()
    binary_counts = counts.reindex(["positive", "negative"]).fillna(0).astype(int)
    return binary_counts[binary_counts > 0]


def plot_business_sentiment_distribution(df: pd.DataFrame, label_col: str):
    counts = get_binary_sentiment_counts(df, label_col)
    fig, ax = plt.subplots(figsize=(6, 4))
    if counts.empty:
        ax.text(0.5, 0.5, "No positive/negative labels available", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    colors = [LABEL_COLORS.get(label, "#4c78a8") for label in counts.index]
    bars = ax.bar(counts.index.str.title(), counts.values, color=colors, width=0.58)
    ax.set_title("Positive vs Negative Review Volume")
    ax.set_ylabel("Count")
    ax.grid(axis="y", alpha=0.18)
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{int(bar.get_height())}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    fig.tight_layout()
    return fig


def extract_top_keywords(df: pd.DataFrame, text_col: str, label_col: str, label: str, top_n: int = 10) -> pd.Series:
    return top_words_by_label(df, text_col, label_col, label).head(top_n)


def generate_business_insight_summary(df: pd.DataFrame, text_col: str, label_col: str) -> str:
    negative_keywords = extract_top_keywords(df, text_col, label_col, "negative", top_n=5)
    positive_keywords = extract_top_keywords(df, text_col, label_col, "positive", top_n=5)

    if negative_keywords.empty and positive_keywords.empty:
        return "There is not enough positive or negative review text yet to generate a business insight summary."

    if negative_keywords.empty:
        positive_terms = ", ".join(positive_keywords.index[:3])
        return f"Customer feedback is largely positive, with common praise around {positive_terms}."

    if positive_keywords.empty:
        negative_terms = ", ".join(negative_keywords.index[:3])
        return f"Most negative feedback is related to {negative_terms}, which may need immediate attention."

    negative_terms = ", ".join(negative_keywords.index[:3])
    positive_terms = ", ".join(positive_keywords.index[:3])
    return (
        f"Most negative feedback is related to {negative_terms}, while positive reviews frequently mention "
        f"{positive_terms}."
    )


def build_word_cloud_html(freqs: pd.Series, label: str) -> str:
    if freqs.empty:
        return "<div class='cloud-wrap'><p>No enough words available for this sentiment.</p></div>"

    random.seed(label)
    max_freq = freqs.max()
    min_freq = freqs.min()
    palette = {
        "positive": ["#2d936c", "#146356", "#51a37b", "#95d5b2"],
        "negative": ["#c44536", "#772e25", "#e26d5c", "#f4a698"],
        "neutral": ["#d88c1f", "#8c5e12", "#e8b95e", "#f7d488"],
    }.get(label, ["#1f4e5f", "#2d936c", "#d88c1f"])

    spans = []
    for idx, (word, freq) in enumerate(freqs.items()):
        if max_freq == min_freq:
            scaled = 28
        else:
            scaled = 16 + ((freq - min_freq) / (max_freq - min_freq)) * 28
        rotation = random.choice([-8, -4, 0, 4, 8])
        color = palette[idx % len(palette)]
        spans.append(
            f"<span class='cloud-word' style='font-size:{scaled:.0f}px;color:{color};transform:rotate({rotation}deg);'>{word}</span>"
        )
    return f"<div class='cloud-wrap'>{''.join(spans)}</div>"


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

    rows = []
    for product in products:
        for start in positive_starts:
            for feature in positive_features[:4]:
                ending = positive_endings[(len(rows) + len(product)) % len(positive_endings)]
                rows.append(
                    {"product": product, "review": f"{start} {product.lower()} with excellent {feature} {ending}.", "sentiment": "positive"}
                )
        for start in negative_starts:
            for feature in negative_features[:4]:
                ending = negative_endings[(len(rows) + len(product)) % len(negative_endings)]
                rows.append(
                    {"product": product, "review": f"{start} {product.lower()} because the {feature} is weak {ending}.", "sentiment": "negative"}
                )
        for start in neutral_starts:
            for feature in neutral_features[:4]:
                ending = neutral_endings[(len(rows) + len(product)) % len(neutral_endings)]
                rows.append(
                    {"product": product, "review": f"{start} {product.lower()} with ordinary {feature} {ending}.", "sentiment": "neutral"}
                )
    return pd.DataFrame(rows)


def load_bundled_product_dataset() -> pd.DataFrame | None:
    frames = [build_demo_product_dataset()]
    dataset_path = PROJECT_ROOT / "data" / "sample_product_reviews.csv"
    if dataset_path.exists():
        try:
            frames.append(pd.read_csv(dataset_path))
        except (OSError, pd.errors.ParserError):
            # The generated dataset keeps the app usable if an optional local CSV is invalid.
            pass
    return pd.concat(frames, ignore_index=True)


def render_header(title: str = "sentiment-analysis-tool", description: str | None = None):
    if description is None:
        description = (
            "Train and compare four classical sentiment models, evaluate performance, "
            "and translate customer feedback into actionable business insights."
        )
    brand_image_data_uri = get_brand_image_data_uri()
    brand_plate_markup = ""
    if brand_image_data_uri is not None:
        brand_plate_markup = (
            '<div class="hero-brand-row">'
            '<div class="brand-plate">'
            '<div class="brand-logo-side">'
            f'<img src="{brand_image_data_uri}" alt="ib brand icon" />'
            "</div>"
            '<div class="brand-name-side">'
            '<span class="brand-chip">ib</span>'
            '<div class="brand-typing-shell">'
            '<span class="brand-typing">ibgaas</span>'
            "</div>"
            "</div>"
            "</div>"
            "</div>"
        )
    hero_markup = (
        '<div class="hero">'
        f"{brand_plate_markup}"
        f'<div class="hero-title">{html.escape(title)}</div>'
        f'<div class="hero-copy">{html.escape(description)}</div>'
        "</div>"
    )
    st.markdown(hero_markup, unsafe_allow_html=True)


def default_model_selection() -> list[str]:
    return list(build_models().keys())


def get_model_confidence(model, inference_text: str, predicted_label: str) -> float | None:
    if hasattr(model, "predict_proba"):
        probabilities = np.asarray(model.predict_proba([inference_text]))
        classes = list(getattr(model, "classes_", []))
        if probabilities.ndim == 2 and probabilities.shape[0] == 1 and predicted_label in classes:
            return float(probabilities[0][classes.index(predicted_label)])

    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function([inference_text]))
        if scores.ndim == 1:
            score = float(scores[0])
            return float(1 / (1 + np.exp(-abs(score))))
        if scores.ndim == 2 and scores.shape[0] == 1:
            row = scores[0]
            shifted = row - np.max(row)
            probabilities = np.exp(shifted) / np.exp(shifted).sum()
            return float(np.max(probabilities))

    return None


def predict_with_trained_model(model_name: str, model, text: str) -> tuple[str, float | None]:
    raw_text = str(text)
    predicted_label = str(build_models()[model_name].predict(model, [raw_text])[0]).lower()
    confidence = get_model_confidence(model, raw_text, predicted_label)
    return predicted_label, confidence


def format_sentiment_label(label: str) -> str:
    return label.capitalize()


def import_speech_recognition_module():
    try:
        return importlib.import_module("speech_recognition")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "SpeechRecognition is unavailable. Install the project dependencies and restart the app."
        ) from error


def transcribe_wav_audio(uploaded_audio_file) -> str:
    sr = import_speech_recognition_module()

    recognizer = sr.Recognizer()
    suffix = Path(uploaded_audio_file.name).suffix.lower() or ".wav"
    temp_path = None

    try:
        uploaded_audio_file.seek(0)
        audio_bytes = uploaded_audio_file.read()
        if not audio_bytes:
            raise RuntimeError("The uploaded audio file is empty. Please upload a valid `.wav` file.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError as exc:
        raise RuntimeError(
            "The speech could not be understood. Try a short, clear English `.wav` recording."
        ) from exc
    except sr.RequestError as exc:
        raise RuntimeError(
            f"Speech recognition service is unavailable right now: {exc}"
        ) from exc
    except (ValueError, EOFError) as exc:
        raise RuntimeError(
            "The uploaded file could not be read as a valid `.wav` audio file."
        ) from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Audio processing failed: {exc}") from exc
    finally:
        try:
            if temp_path is not None:
                Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


def analyze_audio_sentiment_with_improved_model(model, transcript: str) -> dict[str, object]:
    original_transcript = " ".join(str(transcript).split())
    cleaned_transcript = improved_logistic.clean_audio_transcript(original_transcript)
    processed_transcript = improved_logistic.build_audio_debug_text(cleaned_transcript)
    audio_scores = improved_logistic.get_audio_sentiment_scores(cleaned_transcript, processed_transcript)
    meaningful_tokens = [
        token
        for token in re.findall(r"[a-z_]+", processed_transcript)
        if token not in {"question_punct", "emphasis_punct", "mixed_punct"}
    ]

    if len(meaningful_tokens) < 2 and max(audio_scores["positive"], audio_scores["negative"]) < 1.4:
        raise RuntimeError(
            "The transcript is too short or unclear. Please upload clearer audio with a full review sentence."
        )

    predicted_label = str(improved_logistic.predict(model, [cleaned_transcript])[0]).lower()
    confidence = get_model_confidence(model, cleaned_transcript, predicted_label)
    final_label, final_confidence, ambiguous = improved_logistic.postprocess_audio_prediction(
        cleaned_transcript=cleaned_transcript,
        processed_text=processed_transcript,
        predicted_label=predicted_label,
        confidence=confidence,
    )

    return {
        "original_transcript": original_transcript,
        "cleaned_transcript": cleaned_transcript,
        "processed_transcript": processed_transcript,
        "predicted_label": final_label,
        "confidence": final_confidence,
        "ambiguous": ambiguous,
    }


def render_analysis_result(predicted_label: str, confidence: float | None):
    st.success(f"Sentiment analysis result: **{format_sentiment_label(predicted_label)}**")
    if confidence is not None:
        st.metric("Confidence", f"{confidence * 100:.2f}%")
    else:
        st.info("Confidence score is not available for this model.")


def render_try_your_own_text_section(trained_models: dict[str, object], selected_models: list[str]):
    st.markdown("## Live Analysis")
    st.caption("Use the trained classical ML models from your latest run to analyze custom text or short WAV audio clips.")

    centered_left, centered_mid, centered_right = st.columns([0.8, 2.6, 0.8])
    with centered_mid:
        analysis_options = [model_name for model_name in selected_models if model_name in trained_models]
        if not analysis_options:
            st.info("Run at least one model in `Training & Analysis` first to unlock live analysis.")
            return

        ordered_analysis_options = sorted(
            analysis_options,
            key=lambda model_name: (model_name != IMPROVED_LOGISTIC_NAME, model_name),
        )
        default_model_index = (
            ordered_analysis_options.index(IMPROVED_LOGISTIC_NAME)
            if IMPROVED_LOGISTIC_NAME in ordered_analysis_options
            else 0
        )

        with st.container(border=True):
            st.markdown("### Text Analysis")
            st.caption("Choose any trained model for text analysis. Improved Logistic Regression is recommended for slang, emoji, negation, and noisy review text.")
            selected_model = st.selectbox(
                "Choose model",
                options=ordered_analysis_options,
                index=default_model_index,
                key="custom_analysis_model",
            )
            if selected_model == IMPROVED_LOGISTIC_NAME:
                st.info("Recommended model selected: Improved Logistic Regression usually handles emoji, negation, and informal text more reliably.")
            custom_text = st.text_area(
                "Enter text to analyze",
                height=140,
                placeholder="Example: The delivery was quick and the product quality was excellent.",
                key="custom_analysis_text",
            )
            if st.button("Run Text Analysis", use_container_width=True, key="custom_analysis_button"):
                if not custom_text.strip():
                    st.warning("Enter some text to analyze sentiment.")
                else:
                    model = trained_models.get(selected_model)
                    if model is None:
                        st.warning("That model is not available from the latest run. Rerun the analysis with it selected.")
                    else:
                        predicted_label, confidence = predict_with_trained_model(selected_model, model, custom_text)
                        render_analysis_result(predicted_label, confidence)

        st.markdown("")

        with st.container(border=True):
            st.markdown("### Audio Sentiment Analysis")
            st.caption("Upload a short `.wav` file to run audio-to-text sentiment analysis through the trained Improved Logistic Regression pipeline.")
            st.info("Use a clear English `.wav` file with short duration for the best transcription result.")
            st.markdown(f"**Audio model:** `{IMPROVED_LOGISTIC_NAME}`")
            uploaded_audio = st.file_uploader(
                "Upload WAV audio",
                type=["wav"],
                key="audio_sentiment_uploader",
            )
            if uploaded_audio is not None:
                st.markdown("**Audio preview**")
                st.audio(uploaded_audio, format="audio/wav")
            if st.button("Analyze Audio Sentiment", use_container_width=True, key="audio_analysis_button"):
                if uploaded_audio is None:
                    st.warning("Upload a `.wav` audio file to continue.")
                else:
                    model = trained_models.get(IMPROVED_LOGISTIC_NAME)
                    if model is None:
                        st.warning("Improved Logistic Regression is required for audio analysis. Rerun `Training & Analysis` with that model selected.")
                    else:
                        try:
                            extracted_text = transcribe_wav_audio(uploaded_audio)
                        except Exception as exc:
                            st.error(str(exc))
                        else:
                            try:
                                audio_result = analyze_audio_sentiment_with_improved_model(model, extracted_text)
                            except Exception as exc:
                                st.warning(str(exc))
                            else:
                                st.markdown("**Original transcript**")
                                st.write(audio_result["original_transcript"])
                                st.markdown("**Cleaned transcript**")
                                st.write(audio_result["cleaned_transcript"])
                                st.markdown("**Model-ready transcript**")
                                st.code(str(audio_result["processed_transcript"]), language="text")
                                render_analysis_result(
                                    str(audio_result["predicted_label"]),
                                    audio_result["confidence"] if isinstance(audio_result["confidence"], float) else None,
                                )
                                if bool(audio_result["ambiguous"]):
                                    st.warning("Audio text may be ambiguous. Try a clearer or slightly longer spoken review.")


def get_current_analysis_context() -> tuple[pd.DataFrame | None, str | None, str | None, str | None]:
    dataset = st.session_state.get("analysis_dataset")
    dataset_name = st.session_state.get("analysis_dataset_name")
    text_col = st.session_state.get("analysis_text_col")
    label_col = st.session_state.get("analysis_label_col")

    if dataset is not None and dataset_name and text_col and label_col:
        return dataset, dataset_name, text_col, label_col

    fallback = load_bundled_product_dataset()
    if fallback is None:
        return None, None, None, None

    inferred_text, inferred_label = infer_candidate_columns(fallback)
    return fallback, BUNDLED_DATASET_LABEL, inferred_text, inferred_label


def render_analysis_results(
    df: pd.DataFrame,
    dataset_name: str,
    text_col: str,
    label_col: str,
    selected_models: list[str],
    test_size: float,
    random_state: int,
    results: list[ModelResult],
):
    leaderboard = pd.DataFrame(
        {
            "Model": [result.name for result in results],
            "Accuracy": [round(result.accuracy, 4) for result in results],
            "Precision": [round(result.precision, 4) for result in results],
            "Recall": [round(result.recall, 4) for result in results],
            "Weighted F1": [round(result.weighted_f1, 4) for result in results],
            "Train (s)": [round(result.training_seconds, 3) for result in results],
        }
    )
    if not leaderboard.empty:
        leaderboard = leaderboard.sort_values(["Accuracy", "Weighted F1"], ascending=False)

    st.success("Run completed. Review the four-model evaluation below or continue to the Analysis and Business Insights pages.")

    tab_overview, tab_visuals, tab_evaluation = st.tabs(
        ["Overview", "Word Clouds", "Evaluation Details"]
    )

    with tab_overview:
        top_left, top_right = st.columns([1.05, 1.1])
        with top_left:
            st.subheader("Leaderboard")
            if leaderboard.empty:
                st.info("No runnable local models were selected.")
            else:
                st.dataframe(leaderboard, use_container_width=True, hide_index=True)
        with top_right:
            if results:
                comparison_fig = plot_model_comparison(results)
                st.pyplot(comparison_fig, use_container_width=True)
            else:
                st.info("Select at least one model to generate a comparison chart.")

        dist_col, meta_col = st.columns([1.15, 0.85])
        with dist_col:
            distribution_fig = plot_distribution(df[label_col], "Label Distribution")
            st.pyplot(distribution_fig, use_container_width=True)
        with meta_col:
            st.subheader("Run Summary")
            st.write(f"Dataset: `{dataset_name}`")
            st.write(f"Text column: `{text_col}`")
            st.write(f"Label column: `{label_col}`")
            st.write(f"Test split: `{int(test_size * 100)}%`")
            st.write(f"Random seed: `{random_state}`")
            st.write(f"Models compared: `{len(selected_models)}`")

        st.download_button(
            "Download results summary (JSON)",
            data=json.dumps(
                {
                    "dataset": dataset_name,
                    "text_column": text_col,
                    "label_column": label_col,
                    "test_size": test_size,
                    "random_state": random_state,
                    "results": leaderboard.to_dict(orient="records"),
                },
                indent=2,
            ),
            file_name="sentiment_results_summary.json",
            mime="application/json",
        )

    with tab_visuals:
        labels = prepare_labels(df[label_col])[0].dropna().unique().tolist()
        labels = [label for label in ["positive", "neutral", "negative"] if label in labels] + [
            label for label in labels if label not in {"positive", "neutral", "negative"}
        ]
        if not labels:
            st.info("No labels available for word cloud generation.")
        else:
            cloud_columns = st.columns(min(3, max(1, len(labels))))
            for index, label in enumerate(labels):
                with cloud_columns[index % len(cloud_columns)]:
                    st.markdown(f"**{label.title()} word cloud**")
                    freqs = top_words_by_label(df, text_col, label_col, label)
                    st.markdown(build_word_cloud_html(freqs, label), unsafe_allow_html=True)
                    if not freqs.empty:
                        st.dataframe(
                            freqs.rename_axis("word").reset_index(name="count").head(10),
                            hide_index=True,
                            use_container_width=True,
                        )

    with tab_evaluation:
        if leaderboard.empty:
            st.info("No local evaluation results available for the selected models.")
        else:
            best_model = leaderboard.iloc[0]["Model"]
            for result in results:
                with st.expander(result.name, expanded=result.name == best_model):
                    score_col1, score_col2 = st.columns(2)
                    score_col1.metric("Accuracy", f"{result.accuracy:.4f}")
                    score_col2.metric("Weighted F1", f"{result.weighted_f1:.4f}")
                    detail_metrics = st.columns(3)
                    detail_metrics[0].metric("Precision", f"{result.precision:.4f}")
                    detail_metrics[1].metric("Recall", f"{result.recall:.4f}")
                    detail_metrics[2].metric("Training Time", f"{result.training_seconds:.3f}s")

                    matrix_col, report_col = st.columns([1.0, 1.0])
                    with matrix_col:
                        cm_fig = plot_confusion_matrix(result.y_true, result.y_pred, f"{result.name} Confusion Matrix")
                        st.pyplot(cm_fig, use_container_width=True)
                    with report_col:
                        st.markdown("**Classification report**")
                        st.dataframe(result.report.round(4), use_container_width=True)

                    sample_predictions = pd.DataFrame(
                        {
                            "Actual": result.y_true,
                            "Predicted": result.y_pred,
                        }
                    ).head(20)
                    st.markdown("**Sample classifications**")
                    st.dataframe(sample_predictions, use_container_width=True, hide_index=True)


def render_home_page():
    render_header(
        title="sentiment-analysis-tool",
        description=(
            "A polished lightweight ML dashboard for understanding customer feedback, comparing four classical sentiment models, and turning text into business-ready insight."
        ),
    )
    intro_col, highlights_col = st.columns([1.2, 1.0])
    with intro_col:
        st.subheader("What You Can Do Here")
        st.markdown(
            """
            sentiment-analysis-tool helps teams move from raw text to actionable decisions. Use the app to:

            - upload a review dataset and map text and label columns
            - compare four classical ML sentiment models side by side
            - test custom customer comments with trained models in the Analysis page
            - generate business insights, keywords, and word clouds
            - explain sentiment analysis to technical and non-technical stakeholders
            """
        )
    with highlights_col:
        st.subheader("Workspace Map")
        st.markdown(
            """
            - `About`: fundamentals and industry value
            - `Model Details`: strengths and tradeoffs of each approach
            - `Training & Analysis`: upload data, train models, inspect results
            - `Analysis`: try your own text with trained models
            - `Business Insights`: convert sentiment into business signals
            - `Use Cases`: examples across industries
            """
        )

    st.subheader("Recommended Workflow")
    workflow_cols = st.columns(3)
    workflow_cols[0].info("1. Start in `Training & Analysis` to upload or use the bundled dataset and run the selected models.")
    workflow_cols[1].info("2. Move to `Analysis` to test real customer comments using the trained pipelines from the latest run.")
    workflow_cols[2].info("3. Open `Business Insights` to summarize customer pain points and positive drivers.")


def render_about_page():
    render_header(
        title="About Sentiment Analysis",
        description="Understand what sentiment analysis is, why it matters, and how it supports real industry decisions."
    )
    st.subheader("What Is Sentiment Analysis?")
    st.write(
        "Sentiment analysis is the process of identifying the emotional tone inside text such as reviews, "
        "social comments, support tickets, survey responses, and product feedback. It is commonly used to "
        "classify text into positive, negative, or neutral sentiment."
    )

    st.subheader("Why It Matters")
    cols = st.columns(3)
    cols[0].markdown("**Customer Experience**\n\nDetect recurring pain points faster than manual review and prioritize fixes that improve satisfaction.")
    cols[1].markdown("**Brand Monitoring**\n\nTrack perception across channels and spot sentiment shifts before they become larger business problems.")
    cols[2].markdown("**Operational Insight**\n\nConnect negative feedback to areas like delivery, service, packaging, or reliability.")

    st.subheader("Why Industry Uses It")
    st.markdown(
        """
        - `Retail and e-commerce`: understand product quality, delivery, and service feedback at scale.
        - `Banking and fintech`: monitor complaints, trust signals, and support quality.
        - `Telecom and SaaS`: detect churn risk from support conversations and reviews.
        - `Healthcare`: study patient satisfaction themes carefully and responsibly.
        - `Hospitality and travel`: identify drivers of loyalty and operational friction.
        """
    )


def render_model_details_page():
    render_header(
        title="Model Details",
        description="Explore the four classical sentiment models available in the app, including how they work and where they fit best."
    )
    model_cards = [
        (NAIVE_BAYES_NAME, "Fast probabilistic model", "Uses TF-IDF features with a multinomial probability model. It trains quickly and provides a compact classical benchmark for text classification."),
        (LOGISTIC_REGRESSION_NAME, "Reliable linear classifier", "A dependable supervised classifier that performs well on labeled review data and offers a clear, stable benchmark for sentiment tasks."),
        (IMPROVED_LOGISTIC_NAME, "Balanced, sentiment-aware linear classifier", "Extends Logistic Regression with richer negation scope, emoji and emoticon normalization, slang cleanup, expressive phrase handling, punctuation intensity signals, and class balancing so it handles noisy social-media feedback more effectively."),
        (SVM_NAME, "High-margin text classifier", "A strong sparse-text model that often performs well on short reviews and high-dimensional NLP features."),
    ]
    for name, subtitle, description in model_cards:
        st.markdown(f"### {name}")
        st.caption(subtitle)
        st.write(description)

    st.subheader("How to Choose")
    st.markdown(
        """
        - Use `Naive Bayes` when you want a quick, lightweight starting point.
        - Use `Logistic Regression` when you want a reliable classical benchmark.
        - Use `Improved Logistic Regression` when class imbalance, slang, emoji-heavy text, or noisy social-style feedback matters.
        - Use `SVM` when you want a strong sparse-text classifier for review-style data.
        """
    )


def render_training_analysis_page():
    render_header(
        title="Training & Analysis",
        description="Configure the dataset, choose from four classical ML models, and run a compact sentiment experiment with polished comparison views."
    )

    with st.sidebar:
        st.header("Experiment Control")
        data_mode = st.radio(
            "Data source",
            ["Bundled product reviews", "Upload your own dataset"],
            index=0,
        )
        uploaded_file = None
        if data_mode == "Upload your own dataset":
            uploaded_file = st.file_uploader("Upload CSV, JSON, or Excel", type=["csv", "json", "xlsx", "xls"])

        test_size = st.slider("Test split", min_value=0.15, max_value=0.40, value=0.20, step=0.05)
        random_state = st.slider("Random seed", min_value=1, max_value=99, value=42, step=1)
        selected_models = st.multiselect(
            "Models to compare",
            options=get_model_options(),
            default=default_model_selection(),
        )

    if not selected_models:
        st.warning("Select at least one model to continue.")
        return

    if data_mode == "Upload your own dataset":
        if uploaded_file is None:
            st.info("Upload a labeled dataset to begin.")
            return
        try:
            df = read_dataset(uploaded_file)
        except Exception as exc:
            st.error(f"Unable to read the uploaded dataset: {exc}")
            return
        dataset_name = uploaded_file.name
    else:
        df = load_bundled_product_dataset()
        dataset_name = BUNDLED_DATASET_LABEL
        if df is None:
            st.error("Bundled product review dataset was not found.")
            return

    inferred_text, inferred_label = infer_candidate_columns(df)
    if inferred_text is None or inferred_label is None:
        st.error("Could not infer text and label columns from this dataset.")
        return

    missing_values_count = int(df.isna().sum().sum())
    suggested_label_columns = []
    for column in df.columns:
        prepared_labels, _ = prepare_labels(df[column])
        label_counts = prepared_labels[prepared_labels != ""].value_counts()
        if 2 <= len(label_counts) <= 5 and (label_counts.min() >= 2):
            suggested_label_columns.append(column)

    columns = df.columns.tolist()
    default_label = inferred_label
    if suggested_label_columns and inferred_label not in suggested_label_columns:
        default_label = suggested_label_columns[0]

    config_col, overview_col = st.columns([1.35, 1.0], gap="large")
    with config_col:
        with st.container(border=True):
            st.subheader("Experiment Setup")
            text_col = st.selectbox("Text column", columns, index=columns.index(inferred_text))
            label_col = st.selectbox("Label column", columns, index=columns.index(default_label))
            st.caption("Use the sidebar to adjust split, random seed, and the four-model comparison set before running training.")

    prepared_labels, label_note = prepare_labels(df[label_col])
    valid_counts = prepared_labels[prepared_labels != ""].value_counts()
    if valid_counts.empty or len(valid_counts) < 2:
        st.error("The selected label column does not produce at least two sentiment classes. Choose a different label column.")
        return
    if valid_counts.min() < 2:
        st.error("The selected label column has a class with fewer than 2 rows. Choose another label column or add more data.")
        return

    with overview_col:
        with st.container(border=True):
            st.subheader("Dataset Overview")
            st.write(f"Dataset: `{dataset_name}`")
            top_metrics = st.columns(2)
            top_metrics[0].metric("Rows", f"{len(df):,}")
            top_metrics[1].metric("Columns", len(df.columns))
            bottom_metrics = st.columns(2)
            bottom_metrics[0].metric("Classes", int(valid_counts.index.nunique()))
            bottom_metrics[1].metric("Missing Values", f"{missing_values_count:,}")
            readiness = "Ready to train" if len(selected_models) == 4 else "Ready with custom model selection"
            st.success(f"Model readiness: {readiness}")
            st.caption(label_note)
            if suggested_label_columns:
                st.caption(f"Suggested label columns: {', '.join(suggested_label_columns)}")

    imbalance_ratio = get_class_imbalance_ratio(valid_counts)
    summary_col, health_col = st.columns([1.0, 1.0], gap="large")
    with summary_col:
        with st.container(border=True):
            st.subheader("Training Summary")
            st.write(f"Selected models: `{len(selected_models)}`")
            st.write(f"Test split: `{int(test_size * 100)}%`")
            st.write(f"Random seed: `{random_state}`")
            st.write(f"Text column: `{text_col}`")
            st.write(f"Label column: `{label_col}`")
    with health_col:
        with st.container(border=True):
            st.subheader("Dataset Health")
            if imbalance_ratio is not None and imbalance_ratio >= 2:
                st.warning(
                    f"Class imbalance detected. The largest class is about {imbalance_ratio:.1f}x the smallest class."
                )
            else:
                st.info("Class distribution looks reasonably balanced for the current label selection.")
            st.markdown("<div class='metric-note'>These checks are informational only. The training logic remains unchanged.</div>", unsafe_allow_html=True)

    label_summary = pd.DataFrame({"Sentiment": valid_counts.index, "Rows": valid_counts.values})
    current_signature = get_experiment_signature(
        dataset_name=dataset_name,
        text_col=text_col,
        label_col=label_col,
        selected_models=selected_models,
        test_size=test_size,
        random_state=random_state,
        row_count=len(df),
    )

    with st.container(border=True):
        st.subheader("Preview")
        preview_col, label_summary_col = st.columns([1.25, 0.75], gap="large")
        with preview_col:
            st.dataframe(df[[text_col, label_col]].head(12), use_container_width=True, height=320)
        with label_summary_col:
            st.markdown("**Class breakdown**")
            st.dataframe(label_summary, use_container_width=True, hide_index=True)
            st.caption(label_note)

    run_now = st.button("Run Dynamic Sentiment Analysis", type="primary", use_container_width=True)
    if run_now:
        try:
            with st.spinner("Training models and building visuals..."):
                artifacts = train_selected_models(
                    df=df,
                    text_col=text_col,
                    label_col=label_col,
                    selected_models=selected_models,
                    test_size=test_size,
                    random_state=random_state,
                )
        except Exception as exc:
            st.error(str(exc))
            return

        st.session_state["experiment_signature"] = current_signature
        st.session_state["experiment_results"] = artifacts.results
        st.session_state["trained_models"] = artifacts.trained_models
        st.session_state["analysis_dataset"] = df.copy()
        st.session_state["analysis_dataset_name"] = dataset_name
        st.session_state["analysis_text_col"] = text_col
        st.session_state["analysis_label_col"] = label_col
        st.session_state["analysis_selected_models"] = selected_models
        st.session_state["analysis_test_size"] = test_size
        st.session_state["analysis_random_state"] = random_state

    results = []
    if st.session_state.get("experiment_signature") == current_signature:
        results = st.session_state.get("experiment_results", [])

    if not results:
        st.info("Run the analysis once to train the selected models and unlock the Analysis and Business Insights pages.")
        return

    render_analysis_results(
        df=df,
        dataset_name=dataset_name,
        text_col=text_col,
        label_col=label_col,
        selected_models=selected_models,
        test_size=test_size,
        random_state=random_state,
        results=results,
    )


def render_analysis_page():
    render_header(
        title="Analysis",
        description="Try your own text or short WAV audio with the trained four-model sentiment pipeline from your latest analysis run."
    )
    trained_models = st.session_state.get("trained_models", {})
    selected_models = st.session_state.get("analysis_selected_models", default_model_selection())
    if not trained_models:
        st.info("No trained models are available yet. Go to `Training & Analysis`, run an experiment, then return here for custom analysis.")
        return
    render_try_your_own_text_section(trained_models=trained_models, selected_models=selected_models)


def render_business_insights_page():
    render_header(
        title="Business Insights",
        description="Transform review text into business-facing summaries, sentiment signals, and keyword-level findings."
    )
    df, dataset_name, text_col, label_col = get_current_analysis_context()
    if df is None or text_col is None or label_col is None:
        st.error("No dataset is available for insights right now.")
        return

    st.caption(f"Using dataset: `{dataset_name}` with text column `{text_col}` and label column `{label_col}`.")

    sentiment_col, summary_col = st.columns([1.15, 0.85])
    with sentiment_col:
        distribution_fig = plot_business_sentiment_distribution(df, label_col)
        st.pyplot(distribution_fig, use_container_width=True)
    with summary_col:
        st.markdown("### Insight Summary")
        st.info(generate_business_insight_summary(df, text_col, label_col))
        binary_counts = get_binary_sentiment_counts(df, label_col)
        if not binary_counts.empty:
            sentiment_summary = pd.DataFrame(
                {
                    "Sentiment": binary_counts.index.str.title(),
                    "Count": binary_counts.values,
                }
            )
            st.dataframe(sentiment_summary, use_container_width=True, hide_index=True)

    st.markdown("### Top Keywords")
    keyword_col1, keyword_col2 = st.columns(2)
    positive_keywords = extract_top_keywords(df, text_col, label_col, "positive", top_n=10)
    negative_keywords = extract_top_keywords(df, text_col, label_col, "negative", top_n=10)
    with keyword_col1:
        st.markdown("**Positive reviews**")
        if positive_keywords.empty:
            st.info("No positive keywords available.")
        else:
            st.dataframe(
                positive_keywords.rename_axis("Keyword").reset_index(name="Count"),
                use_container_width=True,
                hide_index=True,
            )
    with keyword_col2:
        st.markdown("**Negative reviews**")
        if negative_keywords.empty:
            st.info("No negative keywords available.")
        else:
            st.dataframe(
                negative_keywords.rename_axis("Keyword").reset_index(name="Count"),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("### Word Clouds")
    cloud_col1, cloud_col2 = st.columns(2)
    with cloud_col1:
        st.markdown("**Positive review word cloud**")
        st.markdown(
            build_word_cloud_html(extract_top_keywords(df, text_col, label_col, "positive", top_n=24), "positive"),
            unsafe_allow_html=True,
        )
    with cloud_col2:
        st.markdown("**Negative review word cloud**")
        st.markdown(
            build_word_cloud_html(extract_top_keywords(df, text_col, label_col, "negative", top_n=24), "negative"),
            unsafe_allow_html=True,
        )


def get_class_imbalance_ratio(label_counts: pd.Series) -> float | None:
    if label_counts.empty or label_counts.min() == 0:
        return None
    return float(label_counts.max() / label_counts.min())


def render_use_cases_page():
    render_header(
        title="Use Cases",
        description="See how different industries can apply sentiment analysis for decision-making, automation, and customer experience."
    )
    use_case_cols = st.columns(2)
    with use_case_cols[0]:
        st.markdown(
            """
            ### Customer Support
            - flag high-risk complaints
            - route urgent negative tickets faster
            - monitor service recovery after issue resolution

            ### E-commerce
            - detect product quality complaints
            - compare sentiment across sellers or categories
            - monitor shipping and packaging feedback

            ### Social Listening
            - track brand mood in campaigns
            - identify sudden negative spikes
            - understand message resonance by audience segment
            """
        )
    with use_case_cols[1]:
        st.markdown(
            """
            ### SaaS and Technology
            - analyze feedback from app reviews and support chats
            - identify churn signals from frustrated language
            - evaluate feature launches through customer response

            ### Hospitality and Travel
            - summarize guest pain points
            - compare sentiment by location or service line
            - track reviews for cleanliness, speed, or staff quality

            ### Executive Reporting
            - turn text into simple KPI dashboards
            - explain major complaint themes clearly
            - link qualitative feedback to business outcomes
            """
        )


def main():
    configure_page("sentiment-analysis-tool")
    apply_global_styles()
    render_home_page()


if __name__ == "__main__":
    main()
