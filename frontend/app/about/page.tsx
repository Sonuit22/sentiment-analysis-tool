import { Building2, HeartHandshake, Radar, Scale } from "lucide-react";
import { FeatureCard, PageIntro } from "@/components/UI";

export const metadata = { title: "About" };
export default function AboutPage() {
 return <div className="page-wrap"><PageIntro kicker="About the project" title="Sentiment analysis made inspectable" description="Sentiment Analysis Tool identifies emotional tone in reviews, comments, support tickets, survey responses, and social text while keeping the full research workflow visible." />
 <div className="grid grid-2"><FeatureCard icon={HeartHandshake} title="Customer experience">Detect recurring pain points faster than manual review and prioritize fixes that improve satisfaction.</FeatureCard><FeatureCard icon={Radar} title="Brand monitoring">Track perception across channels and identify sentiment shifts before they become larger problems.</FeatureCard><FeatureCard icon={Building2} title="Operational insight">Connect negative feedback to delivery, service, packaging, reliability, and product-quality themes.</FeatureCard><FeatureCard icon={Scale} title="Responsible interpretation">Treat sentiment as a decision aid, verify important cases, and account for ambiguity, sarcasm, and domain context.</FeatureCard></div>
 <section className="card section"><h2>Why classical machine learning?</h2><p>TF-IDF with linear classifiers offers a fast, explainable, and resource-efficient baseline. These models are well suited to structured experiments, transparent comparisons, and environments where inference cost and reproducibility matter.</p></section></div>;
}
