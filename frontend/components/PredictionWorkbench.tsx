"use client";

import { AudioLines, Gauge, Sparkles, Timer, Waves } from "lucide-react";
import { useState } from "react";
import { predictAudio, predictSentiment } from "@/lib/api";
import type { ModelId, Prediction } from "@/lib/types";
import { ErrorState, LoadingState, Metric } from "./UI";

const models: Array<{ id: ModelId; label: string }> = [
  { id: "improved", label: "Improved Logistic Regression" },
  { id: "logistic", label: "Logistic Regression" },
  { id: "nb", label: "Naive Bayes" },
  { id: "svm", label: "SVM" },
];

export function PredictionWorkbench() {
  const [mode, setMode] = useState<"text" | "audio">("text");
  const [text, setText] = useState("The delivery was quick and the product quality was excellent.");
  const [model, setModel] = useState<ModelId>("improved");
  const [audio, setAudio] = useState<File | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setError("");
    setResult(null);
    if (mode === "text" && !text.trim()) return setError("Enter text to analyze.");
    if (mode === "audio" && !audio) return setError("Choose a WAV file first.");
    setLoading(true);
    try {
      setResult(mode === "text" ? await predictSentiment(text, model) : await predictAudio(audio as File));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-2">
      <section className="card">
        <div className="section-heading">
          <div><h2>Live analysis</h2><p>Use the exact classical ML pipeline from the research application.</p></div>
        </div>
        <div className="segmented" aria-label="Input type">
          <button className={mode === "text" ? "active" : ""} onClick={() => setMode("text")}><Sparkles size={14} /> Text</button>
          <button className={mode === "audio" ? "active" : ""} onClick={() => setMode("audio")}><AudioLines size={14} /> Audio</button>
        </div>
        <div className="form-grid" style={{ marginTop: 18 }}>
          {mode === "text" ? (
            <>
              <div className="field">
                <label htmlFor="model">Model</label>
                <select id="model" className="select" value={model} onChange={(event) => setModel(event.target.value as ModelId)}>
                  {models.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="review">Text to analyze</label>
                <textarea id="review" className="textarea" value={text} maxLength={10000} onChange={(event) => setText(event.target.value)} />
                <small className="muted">{text.length.toLocaleString()} / 10,000 characters</small>
              </div>
            </>
          ) : (
            <div className="field">
              <label htmlFor="audio">WAV recording</label>
              <input id="audio" className="input" type="file" accept=".wav,audio/wav" onChange={(event) => setAudio(event.target.files?.[0] ?? null)} />
              <small className="muted">Audio is transcribed through Google Speech Recognition, then analyzed by Improved Logistic Regression.</small>
            </div>
          )}
          {error && <ErrorState message={error} />}
          <button className="button button-primary" onClick={analyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze sentiment"}<Waves size={17} />
          </button>
        </div>
      </section>
      <section className="card result-card">
        {loading ? <LoadingState label="Running inference" /> : result ? (
          <>
            <span className="eyebrow">Prediction complete</span>
            <h2 className={"sentiment-label sentiment-" + result.sentiment}>{result.sentiment}</h2>
            <div className="grid grid-2">
              <Metric label="Confidence" value={result.confidence == null ? "N/A" : (result.confidence * 100).toFixed(2) + "%"} note="Predicted class" />
              <Metric label="Probability" value={result.probability == null ? "N/A" : result.probability.toFixed(4)} note="Normalized score" />
              <Metric label="Inference time" value={result.inference_time_ms.toFixed(2) + " ms"} note="API model call" />
              <Metric label="Model used" value={result.model_used} note="Selected pipeline" />
            </div>
            {result.probabilities && (
              <div className="section">
                <h3>Class probabilities</h3>
                {Object.entries(result.probabilities).filter(([key]) => key !== "confidence").map(([label, value]) => (
                  <div key={label} style={{ marginTop: 12 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}><span>{label}</span><span>{(value * 100).toFixed(2)}%</span></div>
                    <div style={{ height: 7, background: "var(--surface-soft)", borderRadius: 8, marginTop: 5 }}>
                      <div style={{ width: (value * 100) + "%", height: "100%", background: "var(--brand)", borderRadius: 8 }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            {result.original_transcript && (
              <div className="section">
                <h3>Transcript</h3><p>{result.original_transcript}</p>
                <div className="code-block">{result.processed_transcript}</div>
              </div>
            )}
          </>
        ) : (
          <div className="loading-state">
            <Gauge size={34} />
            <div style={{ textAlign: "center" }}><strong>Your result will appear here</strong><p>Sentiment, confidence, probability, latency, and model details are returned together.</p></div>
          </div>
        )}
      </section>
    </div>
  );
}
