import { TrainingDashboard } from "@/components/TrainingDashboard";
import { PageIntro } from "@/components/UI";
export const metadata={title:"Training analysis"};
export default function TrainingAnalysisPage(){return <div className="page-wrap"><PageIntro kicker="Experiment workspace" title="Training analysis" description="Configure the dataset and test split, run the original four model routines, and inspect every evaluation view from the Streamlit research app."/><TrainingDashboard/></div>;}
