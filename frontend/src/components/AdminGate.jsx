import React, { useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { PrimaryButton } from "./ui-kit";

/**
 * AdminGate
 * – If the current user is an admin, renders children.
 * – Otherwise shows a single passphrase input. Correct passphrase ("duck") swaps
 *   the session into an admin JWT via /api/auth/admin-passphrase.
 */
export default function AdminGate({ children }) {
  const { user, loading, refresh } = useAuth();
  const [passphrase, setPassphrase] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[var(--text-muted)] text-[13px]">
        Loading…
      </div>
    );
  }

  if (user && user.role === "admin") return children;

  const submit = async (e) => {
    e?.preventDefault?.();
    setError("");
    setBusy(true);
    try {
      const { data } = await api.post("/api/auth/admin-passphrase", { passphrase });
      localStorage.setItem("pp_token", data.token);
      await refresh();
    } catch (err) {
      setError(err?.response?.data?.detail || "Couldn't unlock. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-soft)] flex items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[var(--green)] uppercase tracking-[0.16em] hover:opacity-70 mb-6"
          data-testid="admin-gate-back"
        >
          <ArrowLeft size={14} /> Back home
        </Link>
        <div className="bg-white border border-[var(--border)] rounded-[20px] shadow-sm p-8 md:p-10">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center bg-[var(--green-light)] text-[var(--green)] mb-5">
            <ShieldCheck size={26} strokeWidth={1.7} />
          </div>
          <span className="eyebrow">Admin Access</span>
          <h1 className="font-serif text-3xl md:text-4xl font-bold mt-2 text-[var(--green-dark)] leading-tight tracking-tight">
            Say the <span className="italic-green">magic word.</span>
          </h1>
          <p className="text-[var(--text-muted)] mt-3 text-[14px] leading-relaxed">
            Type the team passphrase to open the control panel.
          </p>

          <form onSubmit={submit} className="mt-7 space-y-4">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                Passphrase
              </label>
              <input
                type="password"
                value={passphrase}
                onChange={(e) => setPassphrase(e.target.value)}
                autoFocus
                autoComplete="current-password"
                placeholder="••••"
                data-testid="admin-passphrase-input"
                className="pp-input mt-1.5"
              />
            </div>
            {error && (
              <div className="auth-error" data-testid="admin-gate-error">
                {error}
              </div>
            )}
            <PrimaryButton
              testid="admin-passphrase-submit"
              onClick={submit}
              disabled={busy || !passphrase.trim()}
            >
              {busy ? "Unlocking…" : "Unlock dashboard"}
            </PrimaryButton>
          </form>

          <div className="text-[11px] text-[var(--text-muted)] mt-6 leading-relaxed">
            Not a team member?{" "}
            <Link to="/" className="text-[var(--green)] font-semibold hover:underline">
              Go back home
            </Link>
            .
          </div>
        </div>
      </motion.div>
    </div>
  );
}
