import { Activity, BarChart3, BrainCircuit, FileSearch, Gauge, Layers3 } from "lucide-react";
import { Hero } from "@/components/Hero";
import { FeatureCard, Metric } from "@/components/UI";

export default function HomePage() {
  return <div className="page-wrap">
    <Hero eyebrow="Classical ML, production interface" title="Understand sentiment. Explain every result." description="A complete research and decision workspace for training, comparing, and applying four classical sentiment models to real customer language." primary={{ href: "/prediction", label: "Analyze sentiment" }} />
    <div className="metric-grid section"><Metric label="Model pipelines" value="4" note="Naive Bayes to Linear SVM" /><Metric label="Sentiment classes" value="3" note="Positive | neutral | negative" /><Metric label="Research views" value="10" note="From methodology to insights" /><Metric label="API architecture" value="FastAPI" note="Typed production endpoints" /></div>
    <section className="section"><div className="section-heading"><div><h2>One workspace, complete analysis</h2><p>The original research workflow is preserved as a modern web product.</p></div></div>
      <div className="grid grid-3">
        <FeatureCard icon={BrainCircuit} title="Exact ML pipeline">Use the original TF-IDF and classifier modules without changing label prediction behavior.</FeatureCard>
        <FeatureCard icon={BarChart3} title="Rich evaluation">Compare accuracy, weighted F1, precision, recall, training time, confusion matrices, and reports.</FeatureCard>
        <FeatureCard icon={FileSearch} title="Dataset exploration">Work with bundled product reviews or upload CSV, JSON, XLSX, and XLS data.</FeatureCard>
        <FeatureCard icon={Activity} title="Live inference">Receive sentiment, confidence, probability, inference time, and model provenance.</FeatureCard>
        <FeatureCard icon={Gauge} title="Business interpretation">Turn review volume and keyword patterns into decision-ready insight.</FeatureCard>
        <FeatureCard icon={Layers3} title="Research transparency">Explore preprocessing, methodology, limitations, datasets, and use cases.</FeatureCard>
      </div>
    </section>
  </div>;
}
