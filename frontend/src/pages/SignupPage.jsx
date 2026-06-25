import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { PrimaryButton } from "../components/ui-kit";
import AuthLayout from "./AuthLayout";

export default function SignupPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [marketingOptIn, setMarketingOptIn] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirm) return setError("Passwords don't match.");
    if (!marketingOptIn) return setError("Please agree to receive promotional emails to create your account.");
    setBusy(true);
    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
        phone: phone.trim() || undefined,
        marketing_opt_in: marketingOptIn,
      });
      const next = loc.state?.from || "/dashboard";
      nav(next, { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Couldn't create your account. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout eyebrow="Create an account" title="Welcome to the family." subtitle="Create an account and your first logged-in booking gets 25% off automatically.">
      <form onSubmit={submit} className="space-y-4" data-testid="signup-form">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-soft)] px-4 py-3 text-[13px] text-[var(--green-dark)] leading-relaxed">
          New customers get 25% off their first booking. We will also email the offer to you after signup.
        </div>
        <div>
          <label className="auth-label">Full name</label>
          <input data-testid="signup-name" className="pp-input mt-1.5" placeholder="Your full name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="auth-label">Email</label>
            <input data-testid="signup-email" type="email" className="pp-input mt-1.5" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="auth-label">Phone <span className="text-[var(--text-muted)] font-normal normal-case tracking-normal">(optional)</span></label>
            <input data-testid="signup-phone" className="pp-input mt-1.5" placeholder="(404) 555-0123" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="auth-label">Password</label>
            <input data-testid="signup-password" type="password" className="pp-input mt-1.5" placeholder="At least 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div>
            <label className="auth-label">Confirm</label>
            <input data-testid="signup-confirm" type="password" className="pp-input mt-1.5" placeholder="Repeat password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
          </div>
        </div>
        <label className="tos-row items-start" data-testid="signup-marketing-row">
          <input
            type="checkbox"
            data-testid="signup-marketing"
            checked={marketingOptIn}
            onChange={(e) => setMarketingOptIn(e.target.checked)}
            required
          />
          <span>I agree to receive promotional emails from Pawfect &amp; Pristine, including my 25% first-booking offer. I can unsubscribe at any time.</span>
        </label>
        {error && <div className="auth-error" data-testid="signup-error">{error}</div>}
        <PrimaryButton testid="signup-submit" type="submit" disabled={busy} className="w-full justify-center">
          {busy ? "Creating\u2026" : (<><UserPlus size={16} /> Create my account</>)}
        </PrimaryButton>
        <div className="text-[13px] text-[var(--text-muted)] text-center pt-2">
          Already have one? <Link to="/login" className="text-[var(--green)] font-semibold hover:underline" data-testid="to-login">Sign in</Link>
        </div>
      </form>
    </AuthLayout>
  );
}
