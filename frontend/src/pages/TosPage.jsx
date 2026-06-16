import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import api from "../lib/api";

export default function TosPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/api/tos").then((r) => setData(r.data)).catch(() => {});
  }, []);
  return (
    <div className="min-h-screen bg-[var(--bg-soft)]">
      <div className="max-w-3xl mx-auto px-6 md:px-10 py-10 md:py-14">
        <Link to="/" className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[var(--green)] uppercase tracking-[0.16em] mb-8 hover:opacity-70" data-testid="tos-back">
          <ArrowLeft size={14} /> Back to home
        </Link>
        <div className="mt-2"><span className="eyebrow">Legal</span></div>
        <h1 className="font-serif text-[40px] md:text-[52px] font-bold mt-3 text-[var(--green-dark)] leading-[1.05]">
          Terms of <span className="italic-green">Service.</span>
        </h1>
        {data && (
          <div className="text-[12px] uppercase tracking-[0.18em] text-[var(--text-muted)] mt-3 font-semibold">
            Version {data.version} · Effective {data.effective}
          </div>
        )}
        <div className="mt-8 bg-white border border-[var(--border)] rounded-2xl p-6 md:p-10 shadow-sm">
          <pre className="tos-pre" data-testid="tos-text">{data ? data.text : "Loading\u2026"}</pre>
        </div>
      </div>
    </div>
  );
}
