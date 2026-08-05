"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LeaderboardRow, WordCount } from "@/lib/types";

const colors: Record<string, string> = {
  positive: "#34d399",
  negative: "#fb7185",
  neutral: "#fbbf24",
};
const modelColors = ["#2dd4bf", "#8b5cf6", "#38bdf8", "#fbbf24"];

export function SentimentDistribution({
  data,
}: {
  data: Array<{ sentiment: string; count: number }>;
}) {
  return (
    <div className="chart-wrap" aria-label="Sentiment distribution chart">
      <ResponsiveContainer>
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="sentiment" innerRadius={58} outerRadius={96} paddingAngle={4}>
            {data.map((entry) => <Cell key={entry.sentiment} fill={colors[entry.sentiment] ?? "#8b5cf6"} />)}
          </Pie>
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)", borderRadius: 10 }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ModelScores({
  data,
  metric = "all",
}: {
  data: LeaderboardRow[];
  metric?: "all" | "accuracy" | "weighted_f1" | "training_seconds";
}) {
  const single = metric !== "all";
  return (
    <div className="chart-wrap" aria-label="Model performance chart">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 52 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,.12)" />
          <XAxis dataKey="model" angle={-18} textAnchor="end" interval={0} tick={{ fill: "#95a4b8", fontSize: 10 }} />
          <YAxis domain={metric === "training_seconds" ? [0, "auto"] : [0, 1]} tick={{ fill: "#95a4b8", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)", borderRadius: 10 }} />
          {!single || metric === "accuracy" ? <Bar dataKey="accuracy" name="Accuracy" fill={modelColors[0]} radius={[5, 5, 0, 0]} /> : null}
          {!single || metric === "weighted_f1" ? <Bar dataKey="weighted_f1" name="Weighted F1" fill={modelColors[1]} radius={[5, 5, 0, 0]} /> : null}
          {metric === "training_seconds" ? <Bar dataKey="training_seconds" name="Training seconds" fill={modelColors[2]} radius={[5, 5, 0, 0]} /> : null}
          {!single && <Legend />}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function KeywordChart({ data, tone }: { data: WordCount[]; tone: "positive" | "negative" }) {
  return (
    <div className="chart-wrap" aria-label={tone + " keyword chart"}>
      <ResponsiveContainer>
        <BarChart data={data.slice(0, 8)} layout="vertical" margin={{ left: 12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,.12)" />
          <XAxis type="number" tick={{ fill: "#95a4b8", fontSize: 10 }} />
          <YAxis type="category" dataKey="word" width={82} tick={{ fill: "#95a4b8", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)", borderRadius: 10 }} />
          <Bar dataKey="count" fill={colors[tone]} radius={[0, 5, 5, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
