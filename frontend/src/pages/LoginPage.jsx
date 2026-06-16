import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { PrimaryButton } from "../components/ui-kit";
import AuthLayout from "./AuthLayout";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      const next = loc.state?.from || "/dashboard";
      nav(next, { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Couldn't sign you in. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout eyebrow="Welcome back" title="Sign in to your account." subtitle="See your upcoming visits, schedule a new one, manage your bookings.">
      <form onSubmit={submit} className="space-y-4" data-testid="login-form">
        <div>
          <label className="auth-label">Email</label>
          <input data-testid="login-email" className="pp-input mt-1.5" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label className="auth-label">Password</label>
          <input data-testid="login-password" className="pp-input mt-1.5" type="password" placeholder="Your password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div className="auth-error" data-testid="login-error">{error}</div>}
        <motion.div whileTap={{ scale: 0.99 }}>
          <PrimaryButton testid="login-submit" type="submit" disabled={busy} className="w-full justify-center">
            {busy ? "Signing in\u2026" : (<><LogIn size={16} /> Sign in</>)}
          </PrimaryButton>
        </motion.div>
        <div className="text-[13px] text-[var(--text-muted)] text-center pt-2">
          New here? <Link to="/signup" className="text-[var(--green)] font-semibold underline-offset-2 hover:underline" data-testid="to-signup">Create an account</Link>
        </div>
      </form>
    </AuthLayout>
  );
}
