# Sentiment Analysis Tool

A production-ready sentiment research and prediction application built with Next.js 15, TypeScript, FastAPI, scikit-learn, and Recharts. The migration preserves the original Naive Bayes, Logistic Regression, Improved Logistic Regression, and Linear SVM implementations and exposes the complete research workflow through a responsive SaaS interface.

## Product areas

- Home
- About
- Sentiment Prediction
- Model Details
- Training Analysis
- Model Comparison
- Business Insights
- Research Methodology
- Use Cases
- Developer

The application supports text prediction, optional WAV transcription, built-in and uploaded datasets, model selection, stratified evaluation, leaderboards, accuracy/F1/training-time charts, class distribution, confusion matrices, classification reports, sample predictions, keyword charts, word clouds, and business summaries.

## Architecture

```text
frontend/  Next.js 15 App Router, TypeScript, Recharts, responsive UI
backend/   FastAPI, original model modules, evaluation and insight services
```

The frontend uses a same-origin Next.js proxy under `/api/*`. Set `BACKEND_API_URL` on the frontend deployment to the FastAPI deployment URL.

## Local development

Requirements: Node.js 20.9+, npm, and Python 3.11?3.13.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --reload --port 8000
```

In a second terminal:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
npm install
npm run dev
```

Open `http://localhost:3000`. FastAPI documentation is available locally at `http://127.0.0.1:8000/docs`.

## API

- `GET /health` - service and model readiness
- `POST /predict` - text sentiment, confidence, probability, inference time, and model
- `POST /predict/audio` - WAV transcription and Improved Logistic Regression analysis
- `GET /training-analysis` - default experiment metrics and evaluation data
- `POST /training-analysis/upload` - upload-driven experiment
- `GET /model-comparison` - complete leaderboard and evaluation payload
- `GET /business-insights` - sentiment distribution, keywords, and summary

## Vercel deployment

Vercel recommends deploying monorepo applications as separate related projects.

1. Import this GitHub repository as the backend project and set its Root Directory to `backend`.
2. Deploy the FastAPI project. Its `app.py` entrypoint and `requirements.txt` are detected by the Python runtime.
3. Import the same repository as the frontend project. Keep the repository root selected; the root `vercel.json` builds `frontend/.next`.
4. Add `BACKEND_API_URL=https://YOUR-BACKEND.vercel.app` to the frontend project.
5. Add the frontend production and preview origins to backend `ALLOWED_ORIGINS` if calling the backend directly. The built-in proxy normally keeps browser requests same-origin.

The Vercel Python runtime has a function bundle limit and cold starts. scikit-learn and pandas fit within the documented maximum in typical builds, but verify the final deployment bundle. Each cold backend instance deterministically initializes the same original model training workflow because the source project contains no persisted trained classifier artifact.

## Environment variables

| Variable | Project | Purpose |
| --- | --- | --- |
| `BACKEND_API_URL` | Frontend | FastAPI base URL |
| `ALLOWED_ORIGINS` | Backend | Comma-separated direct browser origins |

No secret is required for core text analysis. Google Speech Recognition is external and may be unavailable in restricted environments.

## Model integrity

Files under `backend/models/` preserve the original training, preprocessing, and prediction logic. Only import paths were made package-safe. No classifier hyperparameters, feature extraction choices, prediction functions, or audio post-processing rules were changed.

The original repository did not include persisted trained classifier files. It included an unused Keras tokenizer that is not referenced by the classical models. The production service therefore caches the same deterministic bundled-data experiment per warm instance and still supports explicit upload-driven experiments.

## Screenshots

Live charts are rendered with Recharts. Historical research charts remain in `images/` for comparison:

![Accuracy comparison](images/new/accuracy_comparison.png)

![F1 comparison](images/new/f1_score_comparison.png)

## License

Released under the [MIT License](LICENSE).

## Acknowledgements

Built with Next.js, React, FastAPI, scikit-learn, pandas, NumPy, Recharts, and SpeechRecognition. See [MIGRATION_REPORT.md](MIGRATION_REPORT.md) for the complete migration record and known deployment considerations.
