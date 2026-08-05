"use client";

import {
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ChevronRight,
  Code2,
  FlaskConical,
  Home,
  Info,
  Menu,
  Moon,
  Network,
  SearchCheck,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const navigation = [
  { href: "/", label: "Home", icon: Home },
  { href: "/about", label: "About", icon: Info },
  { href: "/prediction", label: "Sentiment prediction", icon: Sparkles },
  { href: "/model-details", label: "Model details", icon: Network },
  { href: "/training-analysis", label: "Training analysis", icon: FlaskConical },
  { href: "/model-comparison", label: "Model comparison", icon: BarChart3 },
  { href: "/business-insights", label: "Business insights", icon: BriefcaseBusiness },
  { href: "/research-methodology", label: "Research methodology", icon: BookOpen },
  { href: "/use-cases", label: "Use cases", icon: SearchCheck },
  { href: "/developer", label: "Developer", icon: Code2 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("sat-theme");
    const nextDark = saved ? saved === "dark" : true;
    setDark(nextDark);
    document.documentElement.dataset.theme = nextDark ? "dark" : "light";
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    localStorage.setItem("sat-theme", next ? "dark" : "light");
  }

  return (
    <div className="app-shell">
      <button className="mobile-menu" onClick={() => setOpen(true)} aria-label="Open navigation">
        <Menu size={20} />
      </button>
      {open && <button className="nav-backdrop" onClick={() => setOpen(false)} aria-label="Close navigation" />}
      <aside className={open ? "sidebar sidebar-open" : "sidebar"}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={20} /></div>
          <div>
            <strong>Sentiment</strong>
            <span>Analysis Tool</span>
          </div>
          <button className="sidebar-close" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>
        <nav aria-label="Primary navigation">
          {navigation.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                href={href}
                key={href}
                className={active ? "nav-link active" : "nav-link"}
                onClick={() => setOpen(false)}
              >
                <Icon size={17} />
                <span>{label}</span>
                {active && <ChevronRight size={15} className="nav-chevron" />}
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="status-dot" />
          <div><strong>ML service</strong><span>FastAPI connected</span></div>
        </div>
      </aside>
      <div className="content-shell">
        <header className="topbar">
          <div>
            <span className="eyebrow">Research-grade NLP workspace</span>
          </div>
          <button className="icon-button" onClick={toggleTheme} aria-label="Toggle color theme">
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>
        <main>{children}</main>
        <footer>
          <span>Sentiment Analysis Tool</span>
          <span>Classical ML | FastAPI | Next.js</span>
        </footer>
      </div>
    </div>
  );
}
