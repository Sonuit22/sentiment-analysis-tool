import { BusinessDashboard } from "@/components/BusinessDashboard";
import { PageIntro } from "@/components/UI";
export const metadata={title:"Business insights"};
export default function BusinessInsightsPage(){return <div className="page-wrap"><PageIntro kicker="Decision intelligence" title="Business insights" description="Translate review sentiment, volume, and recurring language into concise operational signals."/><BusinessDashboard/></div>;}
