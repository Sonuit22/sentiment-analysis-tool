import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-wrap">
      <div className="card empty-state">
        <span className="eyebrow">404</span>
        <h1>Page not found</h1>
        <p>The requested research view does not exist.</p>
        <Link className="button button-primary" href="/">Return home</Link>
      </div>
    </div>
  );
}
