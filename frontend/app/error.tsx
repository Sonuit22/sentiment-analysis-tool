"use client";

import { useEffect } from "react";

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return (
    <div className="page-wrap">
      <div className="card empty-state">
        <span className="eyebrow">Something went wrong</span>
        <h1>We could not load this view.</h1>
        <p>{error.message || "Please try again in a moment."}</p>
        <button className="button button-primary" onClick={reset}>Try again</button>
      </div>
    </div>
  );
}
