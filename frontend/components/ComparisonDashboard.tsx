"use client";

import { useEffect, useState } from "react";
import { fetchTraining } from "@/lib/api";
import type { TrainingPayload } from "@/lib/types";
import { ModelScores } from "./AnalyticsCharts";
import { ErrorState, LoadingState, Metric } from "./UI";
import { Leaderboard } from "./TrainingDashboard";

export function ComparisonDashboard() {
  const [data, setData] = useState<TrainingPayload | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { fetchTraining().then(setData).catch((cause) => setError(cause.message)); }, []);
  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState label="Comparing model performance" />;
  const best = data.leaderboard[0];
  return <>
    <div className="metric-grid">
      <Metric label="Top performer" value={best.model} note="Ranked by accuracy and F1" tone="positive" />
      <Metric label="Best accuracy" value={(best.accuracy * 100).toFixed(2) + "%"} note="Held-out set" />
      <Metric label="Best weighted F1" value={best.weighted_f1.toFixed(4)} note="Class-balanced metric" />
      <Metric label="Fastest training" value={Math.min(...data.leaderboard.map((item) => item.training_seconds)).toFixed(3) + "s"} note="Current experiment" />
    </div>
    <section className="card chart-card section"><h2>Side-by-side performance</h2><p>Accuracy and weighted F1 across the four research pipelines.</p><ModelScores data={data.leaderboard} /></section>
    <section className="card section"><h2>Complete scorecard</h2><Leaderboard data={data.leaderboard} /></section>
    <div className="grid grid-2 section">
      {data.leaderboard.map((row) => <article className="card" key={row.model}><span className="eyebrow">{row.model}</span><h3 style={{ marginTop: 10 }}>{row.accuracy >= .8 ? "Strong generalization" : "Research baseline"}</h3><p>Accuracy {(row.accuracy * 100).toFixed(2)}% | Precision {row.precision.toFixed(3)} | Recall {row.recall.toFixed(3)} | Training {row.training_seconds.toFixed(3)}s</p></article>)}
    </div>
  </>;
}
