import type { BusinessPayload, ModelId, ModelName, Prediction, TrainingPayload } from "./types";

const DEFAULT_BACKEND_API_URL = "https://sentiment-analysis-tool-a8nd.onrender.com";
const DIRECT_BACKEND_API_URL = (
  process.env.NEXT_PUBLIC_BACKEND_API_URL?.trim() || DEFAULT_BACKEND_API_URL
).replace(/\/$/, "");

const BACKEND_MODEL_BY_ID: Record<ModelId, ModelName> = {
  improved: "Improved Logistic Regression",
  logistic: "Logistic Regression",
  nb: "Naive Bayes",
  svm: "SVM",
};

export function toBackendModelName(model: ModelId | ModelName): ModelName {
  return BACKEND_MODEL_BY_ID[model as ModelId] ?? (model as ModelName);
}

function errorMessage(payload: unknown, status: number): string {
  if (payload && typeof payload === "object") {
    const record = payload as { detail?: unknown; message?: unknown };
    if (typeof record.detail === "string") return record.detail;
    if (Array.isArray(record.detail)) {
      const details = record.detail.map((item) => {
        if (!item || typeof item !== "object") return String(item);
        const issue = item as { loc?: Array<string | number>; msg?: string };
        const location = issue.loc?.join(".");
        return [location, issue.msg].filter(Boolean).join(": ");
      }).filter(Boolean);
      if (details.length) return details.join("; ");
    }
    if (typeof record.message === "string") return record.message;
  }
  return `API request failed with HTTP ${status}.`;
}

async function responsePayload(response: Response): Promise<unknown> {
  const body = await response.text();
  if (!body) return null;
  try {
    return JSON.parse(body);
  } catch {
    return body;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await responsePayload(response);
  if (!response.ok) {
    const message = typeof payload === "string"
      ? payload
      : errorMessage(payload, response.status);
    console.error("[api-client] Request failed", {
      url: response.url,
      status: response.status,
      message,
      payload,
    });
    throw new Error(message);
  }
  return payload as T;
}

const TRANSIENT_PROXY_STATUSES = new Set([502, 503, 504]);

async function proxyRequest<T>(input: string, init?: RequestInit): Promise<T> {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch(input, init);
      if (attempt === 0 && TRANSIENT_PROXY_STATUSES.has(response.status)) {
        console.warn("[api-client] Retrying transient proxy response", {
          url: input,
          status: response.status,
        });
        await new Promise((resolve) => setTimeout(resolve, 750));
        continue;
      }
      return await parseResponse<T>(response);
    } catch (cause) {
      if (attempt === 0 && cause instanceof TypeError) {
        console.warn("[api-client] Retrying transient proxy network failure", {
          url: input,
          cause,
        });
        await new Promise((resolve) => setTimeout(resolve, 750));
        continue;
      }
      throw cause;
    }
  }
  throw new Error("The API proxy did not return a response.");
}

export async function predictSentiment(text: string, model: ModelId | ModelName): Promise<Prediction> {
  const backendModel = toBackendModelName(model);
  return proxyRequest<Prediction>("/api/predict", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, model: backendModel }),
  });
}

export async function predictAudio(file: File): Promise<Prediction> {
  const body = new FormData();
  body.append("file", file);
  const endpoint = `${DIRECT_BACKEND_API_URL}/predict/audio`;
  try {
    return parseResponse<Prediction>(
      await fetch(endpoint, {
        method: "POST",
        body,
      }),
    );
  } catch (cause) {
    console.error("[api-client] Audio request could not reach the backend", {
      endpoint,
      filename: file.name,
      size: file.size,
      cause,
    });
    if (cause instanceof TypeError) {
      throw new Error(
        "The audio service could not be reached. Check the backend deployment and your network connection.",
      );
    }
    throw cause;
  }
}

export async function fetchTraining(): Promise<TrainingPayload> {
  return proxyRequest<TrainingPayload>("/api/training-analysis", { cache: "no-store" });
}

export async function fetchModelComparison(): Promise<TrainingPayload> {
  return proxyRequest<TrainingPayload>("/api/model-comparison", { cache: "no-store" });
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
    await fetch(`${DIRECT_BACKEND_API_URL}/training-analysis/upload`, {
      method: "POST",
      body,
    }),
  );
}

export async function fetchBusinessInsights(): Promise<BusinessPayload> {
  return proxyRequest<BusinessPayload>("/api/business-insights", { cache: "no-store" });
}
