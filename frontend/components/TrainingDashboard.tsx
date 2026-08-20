"use client";

import { Database, FileUp, RefreshCw, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTraining, uploadTrainingDataset } from "@/lib/api";
import type { Evaluation, ModelName, TrainingPayload } from "@/lib/types";
import { ModelScores, SentimentDistribution } from "./AnalyticsCharts";
import { ErrorState, LoadingState, Metric } from "./UI";

const allModels: ModelName[] = ["Naive Bayes", "Logistic Regression", "Improved Logistic Regression", "SVM"];

export function TrainingDashboard() {
  const [data, setData] = useState<TrainingPayload | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [models, setModels] = useState<ModelName[]>(allModels);
  const [testSize, setTestSize] = useState(0.2);
  const [seed, setSeed] = useState(42);

  useEffect(() => { fetchTraining().then(setData).catch((cause) => setError(cause.message)).finally(() => setLoading(false)); }, []);

  function toggleModel(model: ModelName) {
    setModels((current) => current.includes(model) ? current.filter((item) => item !== model) : [...current, model]);
  }

  async function runUpload() {
    if (!file) return setError("Select a CSV, JSON, XLSX, or XLS dataset.");
    if (!models.length) return setError("Select at least one model.");
    setLoading(true); setError("");
    try { setData(await uploadTrainingDataset(file, models, testSize, seed)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Training failed."); }
    finally { setLoading(false); }
  }

  return (
    <>
      <section className="card">
        <div className="section-heading"><div><h2>Experiment control</h2><p>Use the bundled product reviews or upload a labeled dataset.</p></div><Database size={24} color="var(--brand)" /></div>
        <div className="grid grid-2">
          <div className="form-grid">
            <div className="field"><label htmlFor="dataset">Optional dataset</label><input id="dataset" className="input" type="file" accept=".csv,.json,.xlsx,.xls" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></div>
            <div className="check-grid">{allModels.map((name) => <label className="check-chip" key={name}><input type="checkbox" checked={models.includes(name)} onChange={() => toggleModel(name)} />{name}</label>)}</div>
          </div>
          <div className="form-grid">
            <div className="field"><label htmlFor="split">Test split: {Math.round(testSize * 100)}%</label><input id="split" type="range" min=".15" max=".4" step=".05" value={testSize} onChange={(event) => setTestSize(Number(event.target.value))} /></div>
            <div className="field"><label htmlFor="seed">Random seed</label><input id="seed" className="input" type="number" min="1" max="99" value={seed} onChange={(event) => setSeed(Number(event.target.value))} /></div>
            <div className="form-actions"><button className="button button-primary" onClick={runUpload} disabled={loading}><FileUp size={16} /> Train uploaded data</button><button className="button" onClick={() => location.reload()}><RefreshCw size={16} /> Reset bundled data</button></div>
          </div>
        </div>
        {error && <div style={{ marginTop: 16 }}><ErrorState message={error} /></div>}
      </section>
      {loading ? <LoadingState label="Training models and computing evaluation" /> : data && <TrainingResults data={data} />}
    </>
  );
}

export function TrainingResults({ data }: { data: TrainingPayload }) {
  const [activeModel, setActiveModel] = useState<ModelName>(data.leaderboard[0]?.model ?? "Improved Logistic Regression");
  useEffect(() => {
    if (!data.evaluation.some((item) => item.model === activeModel)) {
      setActiveModel(data.evaluation[0]?.model ?? "Improved Logistic Regression");
    }
  }, [activeModel, data.evaluation]);
  const evaluation = useMemo(() => data.evaluation.find((item) => item.model === activeModel) ?? data.evaluation[0], [activeModel, data]);
  return (
    <>
      <div className="metric-grid section">
        <Metric label="Rows" value={data.dataset.rows.toLocaleString()} note={data.dataset.name} />
        <Metric label="Classes" value={String(data.dataset.classes)} note={data.dataset.label_column} />
        <Metric label="Models evaluated" value={String(data.leaderboard.length)} note="Classical pipelines" />
        <Metric label="Best model" value={data.best_model} note="Accuracy + weighted F1" tone="positive" />
      </div>
      <div className="grid grid-2 section">
        <section className="card chart-card"><h2>Class distribution</h2><p>{data.dataset.label_note}</p><SentimentDistribution data={data.dataset.distribution} /></section>
        <section className="card chart-card"><h2>Accuracy and weighted F1</h2><ModelScores data={data.leaderboard} /></section>
      </div>
      <div className="grid grid-3 section">
        <section className="card chart-card"><h2>Accuracy</h2><ModelScores data={data.leaderboard} metric="accuracy" /></section>
        <section className="card chart-card"><h2>Weighted F1</h2><ModelScores data={data.leaderboard} metric="weighted_f1" /></section>
        <section className="card chart-card"><h2>Training time</h2><ModelScores data={data.leaderboard} metric="training_seconds" /></section>
      </div>
      <section className="card section">
        <div className="section-heading"><div><h2>Leaderboard</h2><p>Weighted evaluation on the held-out test set.</p></div><Trophy color="var(--brand)" /></div>
        <Leaderboard data={data.leaderboard} />
      </section>
      <div className="grid grid-3 section">
        {Object.entries(data.word_clouds).map(([label, words]) => <section className="card" key={label}><h2 style={{ textTransform: "capitalize" }}>{label} word cloud</h2><WordCloud words={words} tone={label} /></section>)}
      </div>
      <section className="card section">
        <h2>Evaluation details</h2>
        <div className="tabs">{data.evaluation.map((item) => <button key={item.model} className={item.model === activeModel ? "active" : ""} onClick={() => setActiveModel(item.model)}>{item.model}</button>)}</div>
        {evaluation && <EvaluationDetail evaluation={evaluation} />}
      </section>
    </>
  );
}

export function Leaderboard({ data }: { data: TrainingPayload["leaderboard"] }) {
  return <div className="table-wrap"><table><thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>Weighted F1</th><th>Train time</th></tr></thead><tbody>{data.map((row, index) => <tr key={row.model}><td>{index === 0 && <span className="badge">Best</span>} {row.model}</td><td>{row.accuracy.toFixed(4)}</td><td>{row.precision.toFixed(4)}</td><td>{row.recall.toFixed(4)}</td><td>{row.weighted_f1.toFixed(4)}</td><td>{row.training_seconds.toFixed(3)}s</td></tr>)}</tbody></table></div>;
}

function WordCloud({ words, tone }: { words: TrainingPayload["word_clouds"][string]; tone: string }) {
  const max = Math.max(...words.map((item) => item.count), 1);
  return <div className={"word-cloud " + tone}>{words.map((item) => <span key={item.word} style={{ fontSize: 13 + item.count / max * 24 }}>{item.word}</span>)}</div>;
}

function EvaluationDetail({ evaluation }: { evaluation: Evaluation }) {
  const maximum = Math.max(...evaluation.confusion_matrix.flat(), 1);
  const reportRows = Object.entries(evaluation.classification_report).filter(([, value]) => typeof value === "object");
  return <div className="grid grid-2">
    <div><h3>Confusion matrix</h3><div className="muted" style={{ marginBottom: 10 }}>Rows are actual labels; columns are predicted labels.</div><div className="confusion-grid" style={{ gridTemplateColumns: "repeat(" + evaluation.labels.length + ", 54px)" }}>{evaluation.confusion_matrix.flatMap((row, rowIndex) => row.map((value, colIndex) => <div title={evaluation.labels[rowIndex] + " -> " + evaluation.labels[colIndex]} className="confusion-cell" style={{ "--heat": String(.08 + value / maximum * .58) } as React.CSSProperties} key={rowIndex + "-" + colIndex}>{value}</div>))}</div><div className="muted" style={{ marginTop: 10 }}>{evaluation.labels.join(" | ")}</div></div>
    <div><h3>Classification report</h3><div className="table-wrap"><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>{reportRows.map(([label, raw]) => { const row = raw as Record<string, number>; return <tr key={label}><td>{label}</td><td>{row.precision?.toFixed(3)}</td><td>{row.recall?.toFixed(3)}</td><td>{row["f1-score"]?.toFixed(3)}</td><td>{row.support}</td></tr>; })}</tbody></table></div></div>
    <div style={{ gridColumn: "1 / -1" }}><h3>Sample classifications</h3><div className="table-wrap"><table><thead><tr><th>Actual</th><th>Predicted</th></tr></thead><tbody>{evaluation.samples.map((sample, index) => <tr key={index}><td>{sample.actual}</td><td>{sample.predicted}</td></tr>)}</tbody></table></div></div>
  </div>;
}
