# Audio Backend Report

## Why the model was unavailable

Both `POST /predict` and `POST /predict/audio` import the same singleton `registry` from `backend/service.py`; there was never a separate audio registry.

The failure had two related causes:

1. Application startup validated Python model files but did not initialize the runtime pipelines. Models were loaded lazily on the first API request.
2. Training analysis can replace the registry with only the selected models. Although the audio endpoint attempted to restore Improved Logistic Regression, it then called `ModelRegistry.predict()`, which performed a second model lookup and retained an unavailable-model rejection.

In the pre-fix source, the rejection was raised by `backend/service.py:412`:

    raise ValueError(
        f"{model_name} is not available. Run training analysis with it selected."
    )

The call reached that code from `backend/app.py:223`, where the audio endpoint invoked `registry.predict(cleaned, IMPROVED_LOGISTIC_NAME)`. The endpoint's `ValueError` handler converted it into HTTP 422 and logged `Audio prediction rejected`.

## Supported audio model

Audio intentionally supports Improved Logistic Regression only. Its module contains the established audio transcript normalization, audio sentiment scoring, and post-processing logic. Naive Bayes, baseline Logistic Regression, and SVM remain available for text prediction but do not implement this audio-specific behavior.

## Fix applied

- The FastAPI lifespan now initializes all four runtime pipelines during startup.
- Startup explicitly verifies that Improved Logistic Regression exists and aborts with a logged startup exception if it cannot load.
- Startup logs list every loaded model and the fixed audio model.
- `ModelRegistry.predict()` now obtains models through `ensure_model_ready()` instead of maintaining a second unavailable-model validation path.
- Text and audio prediction therefore use the same singleton registry and the same model acquisition method.
- The audio endpoint calls `registry.predict()` once and uses that returned sentiment for its unchanged audio post-processing. It no longer accesses or predicts through a separate model object.
- Valid request failures such as a non-WAV file, empty audio, or unintelligible speech still return precise HTTP 422 `detail` messages.

## Verification

- FastAPI lifespan startup loaded all four models and logged `audio_model=Improved Logistic Regression`.
- The startup assertion confirmed Improved Logistic Regression was present before any request.
- Identity verification confirmed `/predict` and `/predict/audio` reference the same `ModelRegistry` singleton.
- The registry was deliberately reduced to Naive Bayes only before each prediction test, reproducing the reported missing-model condition.
- `POST /predict` restored Improved Logistic Regression and returned HTTP 200.
- `POST /predict/audio` restored the same model and returned HTTP 200 with sentiment, confidence, probabilities, inference time, and `model_used: Improved Logistic Regression`.
- A non-WAV multipart request returned HTTP 422 with `{"detail":"Upload a WAV audio file."}`.
- Python compilation and `git diff --check` completed successfully.
