import { ComparisonDashboard } from "@/components/ComparisonDashboard";
import { PageIntro } from "@/components/UI";
export const metadata={title:"Model comparison"};
export default function ModelComparisonPage(){return <div className="page-wrap"><PageIntro kicker="Benchmark" title="Model comparison" description="Compare generalization quality and computational tradeoffs across the complete classical ML model set."/><ComparisonDashboard/></div>;}
