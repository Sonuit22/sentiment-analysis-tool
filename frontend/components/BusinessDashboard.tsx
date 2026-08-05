"use client";

import { useEffect, useState } from "react";
import { fetchBusinessInsights } from "@/lib/api";
import type { BusinessPayload } from "@/lib/types";
import { KeywordChart, SentimentDistribution } from "./AnalyticsCharts";
import { ErrorState, LoadingState } from "./UI";

export function BusinessDashboard() {
  const [data, setData] = useState<BusinessPayload | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { fetchBusinessInsights().then(setData).catch((cause) => setError(cause.message)); }, []);
  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState label="Building business insight" />;
  return (
    <>
      <div className="grid grid-2">
        <section className="card chart-card"><h2>Sentiment volume</h2><p>Positive, negative, and neutral review mix.</p><SentimentDistribution data={data.distribution} /></section>
        <section className="card"><span className="eyebrow">Executive summary</span><h2 style={{ marginTop: 10 }}>What customers are saying</h2><div className="insight-callout">{data.summary}</div>
          <div className="section"><h3>Decision lens</h3><p>Use recurring negative themes to prioritize product and service fixes, then monitor positive drivers as retention signals.</p></div>
        </section>
      </div>
      <div className="grid grid-2 section">
        <section className="card chart-card"><h2>Positive review keywords</h2><KeywordChart data={data.positive_keywords} tone="positive" /></section>
        <section className="card chart-card"><h2>Negative review keywords</h2><KeywordChart data={data.negative_keywords} tone="negative" /></section>
      </div>
      <div className="grid grid-2 section">
        <WordCloud title="Positive word cloud" words={data.positive_keywords} tone="positive" />
        <WordCloud title="Negative word cloud" words={data.negative_keywords} tone="negative" />
      </div>
    </>
  );
}
function WordCloud({ title, words, tone }: { title: string; words: BusinessPayload["positive_keywords"]; tone: string }) {
  const max = Math.max(...words.map((item) => item.count), 1);
  return <section className="card"><h2>{title}</h2><div className={"word-cloud " + tone}>{words.map((item) => <span key={item.word} style={{ fontSize: 15 + (item.count / max) * 27 }}>{item.word}</span>)}</div></section>;
}
