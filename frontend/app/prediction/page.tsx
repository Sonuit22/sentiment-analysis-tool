import { PageIntro } from "@/components/UI";
import { PredictionWorkbench } from "@/components/PredictionWorkbench";
export const metadata = { title: "Sentiment prediction" };
export default function PredictionPage(){return <div className="page-wrap"><PageIntro kicker="Live inference" title="Sentiment prediction" description="Analyze text with any trained research pipeline or transcribe a short WAV recording through the improved logistic model."/><PredictionWorkbench/></div>;}
