import type { BusinessPayload, ModelId, ModelName, Prediction, TrainingPayload } from "./types";

const BACKEND_MODEL_BY_ID: Record<ModelId, ModelName> = {
  improved: "Improved Logistic Regression",
  logistic: "Logistic Regression",
  nb: "Naive Bayes",
  svm: "SVM",
};

export function toBackendModelName(model: ModelId | ModelName): ModelName {
  return BACKEND_MODEL_BY_ID[model as ModelId] ?? (model as ModelName);
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "The request could not be completed.");
  }
  return payload as T;
}

export async function predictSentiment(text: string, model: ModelId | ModelName): Promise<Prediction> {
  const backendModel = toBackendModelName(model);
  return parseResponse<Prediction>(
    await fetch("/api/predict", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, model: backendModel }),
    }),
  );
}

export async function predictAudio(file: File): Promise<Prediction> {
  const body = new FormData();
  body.append("file", file);
  return parseResponse<Prediction>(
    await fetch("/api/predict/audio", { method: "POST", body }),
  );
}

export async function fetchTraining(): Promise<TrainingPayload> {
  return parseResponse<TrainingPayload>(
    await fetch("/api/training-analysis", { cache: "no-store" }),
  );
}

export async function uploadTrainingDataset(
  file: File,
  models: ModelName[],
  testSize: number,
  randomState: number,
): Promise<TrainingPayload> {
  const body = new FormData();
  body.append("file", file);
  body.append("models", models.join(","));
  body.append("test_size", String(testSize));
  body.append("random_state", String(randomState));
  return parseResponse<TrainingPayload>(
    await fetch("/api/training-analysis/upload", { method: "POST", body }),
  );
}

export async function fetchBusinessInsights(): Promise<BusinessPayload> {
  return parseResponse<BusinessPayload>(
    await fetch("/api/business-insights", { cache: "no-store" }),
  );
}
