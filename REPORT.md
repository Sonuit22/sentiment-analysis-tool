# Backend Runtime Audit Report

## Scope

Only the FastAPI backend was audited. No frontend source, Vercel configuration, Render configuration, or deployment settings were modified.

Audited files:

- `backend/app.py`
- `backend/service.py`
- `backend/schemas.py`
- `backend/models/naive_bayes.py`
- `backend/models/logistic.py`
- `backend/models/improved_logistic.py`
- `backend/models/svm.py`
- `backend/utils/preprocessing.py`

## Root cause

The reported failure pattern matches the backend's former shared-model-registry bug. A training-analysis request that selected only Naive Bayes could replace the global runtime registry with that subset. Naive Bayes would continue working while Logistic Regression, Improved Logistic Regression, SVM, and audio prediction became unavailable.

The current backend revision already contains the required runtime correction:

- `backend/app.py:81` initializes every runtime model during FastAPI startup.
- `backend/app.py:213` runs uploaded-dataset experiments in a separate `ModelRegistry`, so training analysis cannot overwrite the production prediction registry.
- `backend/service.py:304` restores an individually missing runtime model with `ensure_model_ready()`.
- `backend/service.py:416` makes every text prediction use that recovery path.
- `backend/app.py:276` makes audio prediction use the same shared registry and Improved Logistic Regression pipeline as `/predict`.

The alleged current HTTP 500 responses were not reproducible. At audit time, both local FastAPI and the deployed Render backend returned HTTP 200 for every model and for a public WAV fixture.

## Model and preprocessing audit

These models are source-defined scikit-learn pipelines trained in memory from the bundled runtime dataset. There are no serialized model pickle files in version control and none are loaded at runtime.

| Model | Tracked model source | Pipeline | Preprocessing | Direct prediction | FastAPI `/predict` | Deployed Render |
|---|---|---|---|---:|---:|---:|
| Naive Bayes | `backend/models/naive_bayes.py` | TF-IDF + MultinomialNB | `clean_text` | Pass | 200 | 200 |
| Logistic Regression | `backend/models/logistic.py` | TF-IDF + LogisticRegression | `clean_text` | Pass | 200 | 200 |
| Improved Logistic Regression | `backend/models/improved_logistic.py` | TF-IDF + LogisticRegression | `preprocess_text` | Pass | 200 | 200 |
| SVM | `backend/models/svm.py` | character TF-IDF + LinearSVC | `clean_text` | Pass | 200 | 200 |

All four model modules imported, trained, and predicted successfully. Confidence/probability generation also completed successfully for every model, including softmax-normalized SVM decision scores.

### Tokenizer artifact

`backend/models/tokenizer.pkl` exists only as a local, ignored legacy artifact (`.gitignore` excludes `*.pkl`). It is not included in the deployed repository and is not used by any active classical pipeline.

Loading this unused local artifact directly produces the exact exception:

```text
ModuleNotFoundError: No module named 'keras'
```

Adding Keras/TensorFlow would be an unnecessary production dependency and would not affect any prediction. The active TF-IDF vectorizers are constructed inside the four model pipelines; no tokenizer pickle is required.

## Missing-model recovery verification

A fresh registry was deliberately trained with only Naive Bayes. Predictions were then requested in this order:

1. Naive Bayes
2. Logistic Regression
3. Improved Logistic Regression
4. SVM

Each missing pipeline was rebuilt successfully by `ensure_model_ready()`. The final loaded-model list contained all four models. No exception was suppressed.

## Endpoint verification

### Startup and health

- Command: `uvicorn app:app --host 127.0.0.1 --port 8000`
- Result: startup passed.
- Startup logs confirmed all four models loaded.
- `GET /health`: HTTP 200 with `models_ready: true` and all four model names.

### Text prediction

Request text: `I absolutely love this product`

| Requested model | Local direct | Local FastAPI/TestClient | Local Uvicorn | Deployed Render |
|---|---:|---:|---:|---:|
| Naive Bayes | Pass | 200 | 200 | 200 |
| Logistic Regression | Pass | 200 | 200 | 200 |
| Improved Logistic Regression | Pass | 200 | 200 | 200 |
| SVM | Pass | 200 | 200 | 200 |

Every response contained `sentiment`, `confidence`, `probability`, `probabilities`, `inference_time_ms`, and the exact `model_used` value.

### Audio prediction

The public `examples/english.wav` fixture from the SpeechRecognition project was used instead of personal audio.

- WAV decoding: passed.
- Google Speech Recognition: passed; the transcript was `1 2 3` locally and `1 2` on Render. This minor difference is normal for an external speech service.
- Audio transcript cleanup: passed.
- Improved Logistic Regression preprocessing: passed.
- Prediction through the shared registry: passed.
- Local FastAPI/TestClient `POST /predict/audio`: HTTP 200.
- Deployed Render `POST /predict/audio`: HTTP 200.
- Returned `model_used`: `Improved Logistic Regression`.

An actual local Uvicorn process started inside the restricted test sandbox returned HTTP 503 because that sandbox denied the server process's outbound Google connection (`ConnectionRefusedError [WinError 10061]`). The same code succeeded when network access was permitted and succeeded on Render, confirming that this was a test-environment network restriction rather than an application defect. The traceback was logged in full.

## Files changed

- Added `REPORT.md`.
- No backend runtime source change was necessary because the current backend already contains the shared-registry and audio-model fixes and all required endpoints pass.
- No frontend or deployment file was changed.

## Deployment readiness

The audited backend revision is ready for continued Render deployment. All four text models and the audio endpoint currently pass against the deployed backend. If another HTTP 500 is observed, retain the Render traceback, request timestamp, model name, and input text; the current direct endpoint results do not reproduce such a failure.
