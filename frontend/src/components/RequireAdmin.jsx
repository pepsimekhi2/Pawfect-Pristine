import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function RequireAdmin({ children }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-[var(--text-muted)] text-[13px]">Loading…</div>;
  }
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (user.role !== "admin") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <div className="text-[56px]">🔒</div>
        <h2 className="font-serif text-3xl text-[var(--green-dark)] mt-4">Admin only.</h2>
        <p className="text-[var(--text-muted)] mt-2 text-[14px]">This area is for the Pawfect &amp; Pristine team.</p>
      </div>
    );
  }
  return children;
}
