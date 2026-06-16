import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { PrimaryButton, OutlineButton } from "./ui-kit";
import { LayoutDashboard, LogIn } from "lucide-react";

export default function HeaderAuth() {
  const { user, loading } = useAuth();
  if (loading) return <span className="text-[12px] text-[var(--text-muted)]">…</span>;
  if (user) {
    return (
      <Link to="/dashboard" data-testid="nav-dashboard">
        <PrimaryButton testid="header-dashboard-btn">
          <LayoutDashboard size={14} /> Dashboard
        </PrimaryButton>
      </Link>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <Link to="/login" data-testid="nav-login"><OutlineButton testid="header-login-btn"><LogIn size={14} /> Sign in</OutlineButton></Link>
      <Link to="/book" data-testid="nav-book"><PrimaryButton testid="header-book-btn">Book</PrimaryButton></Link>
    </div>
  );
}
