import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-muted)] text-[13px]">Loading…</div>;
  }
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  return children;
}
