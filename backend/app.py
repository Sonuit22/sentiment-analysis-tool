from __future__ import annotations

import logging
import os
import tempfile
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import speech_recognition as sr
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
MODELS_DIR = BACKEND_DIR / "models"
TOKENIZER_PATH = MODELS_DIR / "tokenizer.pkl"
REQUIRED_MODEL_FILES = (
    "naive_bayes.py",
    "logistic.py",
    "improved_logistic.py",
    "svm.py",
)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sentiment_analysis.api")

if __package__:
    from .models import improved_logistic
    from .schemas import HealthResponse, PredictRequest, PredictResponse
    from .service import IMPROVED_LOGISTIC_NAME, MODEL_NAMES, infer_candidate_columns, registry
else:
    from models import improved_logistic
    from schemas import HealthResponse, PredictRequest, PredictResponse
    from service import IMPROVED_LOGISTIC_NAME, MODEL_NAMES, infer_candidate_columns, registry


def validate_runtime_files() -> None:
    missing = [
        str(MODELS_DIR / filename)
        for filename in REQUIRED_MODEL_FILES
        if not (MODELS_DIR / filename).is_file()
    ]
    if missing:
        raise RuntimeError(f"Required model files are missing: {', '.join(missing)}")
    logger.info("Validated model directory: %s", MODELS_DIR)
    if TOKENIZER_PATH.is_file():
        logger.info("Optional tokenizer found at %s; active classical pipelines do not use it", TOKENIZER_PATH)
    else:
        logger.info("No tokenizer artifact present; none is required by the active models")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting Sentiment Analysis Tool API")
    logger.info("Backend directory: %s", BACKEND_DIR)
    logger.info("Project root: %s", PROJECT_ROOT)
    try:
        validate_runtime_files()
    except Exception:
        logger.critical("Backend startup validation failed:\n%s", traceback.format_exc())
        raise
    logger.info("API startup complete; models_ready=%s", registry.ready)
    yield
    logger.info("Sentiment Analysis Tool API stopped")


app = FastAPI(
    title="Sentiment Analysis Tool API",
    description="Production API for prediction, training evaluation, and business insight.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    value.strip()
    for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if value.strip()
]
vercel_origin_regex = r"https://(?:[a-z0-9-]+\.)*vercel\.app"
configured_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", "").strip()
origin_regex = (
    rf"(?:{vercel_origin_regex})|(?:{configured_origin_regex})"
    if configured_origin_regex
    else vercel_origin_regex
)
logger.info("CORS origins=%s origin_regex=%s", origins, origin_regex)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.error(
            "Unhandled exception during %s %s:\n%s",
            request.method,
            request.url.path,
            traceback.format_exc(),
        )
        raise
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="sentiment-analysis-tool-api",
        models_ready=registry.ready,
        available_models=MODEL_NAMES,
        version="1.0.0",
    )


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    logger.info(
        "Prediction requested: model=%s characters=%d",
        payload.model,
        len(payload.text),
    )
    try:
        result = PredictResponse(**registry.predict(payload.text, payload.model))
        logger.info("Prediction completed: model=%s sentiment=%s", payload.model, result.sentiment)
        return result
    except ValueError as exc:
        logger.warning("Prediction rejected: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.error("Prediction failed:\n%s", traceback.format_exc())
        raise


@app.get("/training-analysis")
def training_analysis() -> dict:
    return registry.training_payload()


@app.post("/training-analysis/upload")
async def training_analysis_upload(
    file: UploadFile = File(...),
    text_column: str = Form(""),
    label_column: str = Form(""),
    models: str = Form(",".join(MODEL_NAMES)),
    test_size: float = Form(0.2),
    random_state: int = Form(42),
) -> dict:
    try:
        content = await file.read()
        if not content:
            raise ValueError("The uploaded dataset is empty.")
        dataframe = registry.load_uploaded_dataset(file.filename or "dataset.csv", content)
        inferred_text, inferred_label = infer_candidate_columns(dataframe)
        selected_text = text_column or inferred_text
        selected_label = label_column or inferred_label
        if not selected_text or not selected_label:
            raise ValueError("Could not infer text and label columns.")
        selected_models = [name.strip() for name in models.split(",") if name.strip()]
        return registry.train(
            dataframe,
            selected_text,
            selected_label,
            selected_models,
            test_size,
            random_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()


@app.get("/model-comparison")
def model_comparison() -> dict:
    return registry.training_payload()


@app.get("/business-insights")
def business_insights() -> dict:
    return registry.business_insights()


@app.post("/predict/audio")
async def predict_audio(file: UploadFile = File(...)) -> dict:
    logger.info("Audio prediction requested: filename=%s", file.filename)
    if not (file.filename or "").lower().endswith(".wav"):
        raise HTTPException(status_code=422, detail="Upload a WAV audio file.")
    try:
        model = registry.ensure_model_ready(IMPROVED_LOGISTIC_NAME)
        content = await file.read()
        if not content:
            raise ValueError("The uploaded audio file is empty.")
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_file.write(content)
                temp_path = audio_file.name
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                transcript = recognizer.recognize_google(recognizer.record(source))
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)
        original = " ".join(transcript.split())
        cleaned = improved_logistic.clean_audio_transcript(original)
        processed = improved_logistic.build_audio_debug_text(cleaned)
        scores = improved_logistic.get_audio_sentiment_scores(cleaned, processed)
        predicted = str(improved_logistic.predict(model, [cleaned])[0]).lower()
        prediction = registry.predict(cleaned, IMPROVED_LOGISTIC_NAME)
        final_label, final_confidence, ambiguous = improved_logistic.postprocess_audio_prediction(
            cleaned_transcript=cleaned,
            processed_text=processed,
            predicted_label=predicted,
            confidence=prediction["confidence"],
        )
        return {
            **prediction,
            "sentiment": final_label,
            "confidence": final_confidence,
            "probability": final_confidence,
            "original_transcript": original,
            "cleaned_transcript": cleaned,
            "processed_transcript": processed,
            "ambiguous": ambiguous,
            "sentiment_scores": scores,
        }
    except sr.UnknownValueError as exc:
        logger.warning("Audio transcription could not understand the uploaded file")
        raise HTTPException(status_code=422, detail="Speech could not be understood.") from exc
    except sr.RequestError as exc:
        logger.exception("Speech recognition service request failed")
        raise HTTPException(status_code=503, detail="Speech recognition is unavailable.") from exc
    except ValueError as exc:
        logger.warning("Audio prediction rejected: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.error("Audio prediction failed:\n%s", traceback.format_exc())
        raise
    finally:
        await file.close()


def run() -> None:
    import uvicorn

    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    logger.info("Launching Uvicorn on http://%s:%d", host, port)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
