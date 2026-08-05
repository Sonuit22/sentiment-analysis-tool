export type ModelName =
  | "Naive Bayes"
  | "Logistic Regression"
  | "Improved Logistic Regression"
  | "SVM";

export type ModelId = "improved" | "logistic" | "nb" | "svm";

export interface Prediction {
  sentiment: string;
  confidence: number | null;
  probability: number | null;
  probabilities: Record<string, number> | null;
  inference_time_ms: number;
  model_used: ModelName;
  original_transcript?: string;
  cleaned_transcript?: string;
  processed_transcript?: string;
  ambiguous?: boolean;
}

export interface LeaderboardRow {
  model: ModelName;
  accuracy: number;
  precision: number;
  recall: number;
  weighted_f1: number;
  training_seconds: number;
}

export interface Evaluation {
  model: ModelName;
  labels: string[];
  confusion_matrix: number[][];
  classification_report: Record<string, Record<string, number> | number>;
  samples: Array<{ actual: string; predicted: string }>;
}

export interface WordCount {
  word: string;
  count: number;
}

export interface TrainingPayload {
  dataset: {
    name: string;
    rows: number;
    columns: number;
    classes: number;
    missing_values: number;
    text_column: string;
    label_column: string;
    label_note: string;
    distribution: Array<{ sentiment: string; count: number }>;
  };
  leaderboard: LeaderboardRow[];
  evaluation: Evaluation[];
  word_clouds: Record<string, WordCount[]>;
  best_model: ModelName;
}

export interface BusinessPayload {
  distribution: Array<{ sentiment: string; count: number }>;
  positive_keywords: WordCount[];
  negative_keywords: WordCount[];
  summary: string;
}
