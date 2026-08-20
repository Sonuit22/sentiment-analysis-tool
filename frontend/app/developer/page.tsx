import { Boxes, Code2, Github, ServerCog } from "lucide-react";
import { FeatureCard, PageIntro } from "@/components/UI";
export const metadata={title:"Developer"};
export default function DeveloperPage(){return <div className="page-wrap"><PageIntro kicker="Engineering reference" title="Built for extension and deployment" description="A typed Next.js interface, an ASGI FastAPI service, and isolated model modules make the research application easier to test, operate, and evolve."/>
<div className="grid grid-3"><FeatureCard icon={Code2} title="Next.js 15">App Router, TypeScript, responsive server-rendered pages, interactive client components, metadata, and resilient error states.</FeatureCard><FeatureCard icon={ServerCog} title="FastAPI">Typed prediction and health contracts plus endpoints for training evaluation, uploads, audio, comparison, and insights.</FeatureCard><FeatureCard icon={Boxes} title="Vercel + Render">The frontend and API deploy independently so each service receives the correct production runtime.</FeatureCard></div>
<section className="card section"><h2>API contract</h2><div className="code-block">{`POST /predict
{"text":"Excellent build quality","model":"Improved Logistic Regression"}

GET /health
GET /training-analysis
POST /training-analysis/upload
GET /model-comparison
GET /business-insights
POST /predict/audio`}</div></section>
<section className="card section"><h2>Local services</h2><div className="code-block">python -m uvicorn backend.app:app --reload --port 8000{"\n"}npm run dev</div><p style={{marginTop:16}}>Set <code>BACKEND_API_URL</code> for the frontend server. Production deployment details are included in the repository README.</p></section>
<section className="card section"><div style={{display:"flex",gap:12,alignItems:"center"}}><Github/><div><h3>Open-source ready</h3><p>MIT licensed with migration notes, health checks, and reproducible setup instructions.</p></div></div></section></div>;}
