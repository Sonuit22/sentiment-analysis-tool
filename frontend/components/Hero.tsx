import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

export function Hero({
  eyebrow,
  title,
  description,
  primary,
}: {
  eyebrow: string;
  title: string;
  description: string;
  primary?: { href: string; label: string };
}) {
  return (
    <section className="hero">
      <div className="hero-glow hero-glow-one" />
      <div className="hero-glow hero-glow-two" />
      <div className="hero-grid" />
      <div className="hero-content">
        <div className="pill"><Sparkles size={14} /> {eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
        {primary && (
          <Link href={primary.href} className="button button-primary">
            {primary.label}<ArrowRight size={17} />
          </Link>
        )}
      </div>
      <div className="hero-orbit" aria-hidden="true">
        <span className="orbit orbit-one" />
        <span className="orbit orbit-two" />
        <div className="hero-core"><Sparkles size={30} /></div>
      </div>
    </section>
  );
}
