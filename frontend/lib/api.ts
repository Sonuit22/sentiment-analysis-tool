import type { BusinessPayload, ModelName, Prediction, TrainingPayload } from "./types";

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "The request could not be completed.");
  }
  return payload as T;
}

export async function predictSentiment(text: string, model: ModelName): Promise<Prediction> {
  return parseResponse<Prediction>(
    await fetch("/api/predict", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, model }),
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
