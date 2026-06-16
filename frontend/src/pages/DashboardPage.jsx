import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CalendarPlus, LogOut, Sparkles, X, MapPin, Clock } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { PrimaryButton, OutlineButton } from "../components/ui-kit";
import MonthCalendar from "../components/MonthCalendar";

function StatusPill({ status }) {
  const s = status || "scheduled";
  return <span className={`status-pill status-${s}`}>{s}</span>;
}

function PayBadge({ b }) {
  const ps = b.payment_status || "unpaid";
  const label = {
    paid_full: "Paid in full",
    paid_half: "Half paid",
    unpaid: "Pay on arrival",
  }[ps] || ps;
  return <span className={`pay-pill pay-${ps}`}>{label}</span>;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [upcoming, setUpcoming] = useState([]);
  const [past, setPast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [u, a] = await Promise.all([
        api.get("/api/bookings/upcoming"),
        api.get("/api/bookings/me"),
      ]);
      setUpcoming(u.data || []);
      const upcomingIds = new Set((u.data || []).map((x) => x.id));
      setPast((a.data || []).filter((x) => !upcomingIds.has(x.id)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onCancel = async (id) => {
    if (!window.confirm("Cancel this booking? You'll need to re-book if you change your mind.")) return;
    setBusyId(id);
    try {
      await api.post(`/api/bookings/${id}/cancel`);
      await load();
    } catch (e) {
      alert("Couldn't cancel. Try again.");
    } finally { setBusyId(null); }
  };

  const onLogout = async () => { await logout(); nav("/"); };

  const nextOne = upcoming[0];

  return (
    <div className="min-h-screen bg-[var(--bg-soft)]">
      <header className="bg-white border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5" data-testid="dashboard-logo">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--green)] text-white"><span className="text-lg leading-none">🐾</span></div>
            <div className="flex flex-col leading-tight">
              <span className="font-serif text-[17px] font-bold text-[var(--green-dark)]">Pawfect &amp; Pristine</span>
              <span className="text-[9px] uppercase tracking-[0.18em] font-medium text-[var(--green-muted)]">Your dashboard</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden md:inline text-[13px] text-[var(--text-muted)]">Hi, <span className="font-medium text-[var(--text)]">{user?.name?.split(" ")[0]}</span></span>
            <button onClick={onLogout} className="text-[13px] font-semibold text-[var(--text-muted)] hover:text-[var(--green-dark)] inline-flex items-center gap-1.5" data-testid="dashboard-logout">
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 md:px-10 py-10 md:py-14">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap items-end justify-between gap-4 mb-8">
          <div>
            <span className="eyebrow">Your dashboard</span>
            <h1 className="font-serif text-[36px] md:text-[48px] font-bold mt-2 text-[var(--green-dark)] leading-tight">
              Welcome back, <span className="italic-green">{user?.name?.split(" ")[0]}.</span>
            </h1>
            <p className="text-[var(--text-muted)] mt-2 text-[15px] max-w-lg">
              Here's what's coming up. You can schedule a new visit anytime.
            </p>
          </div>
          <Link to="/book" data-testid="dashboard-book-cta"><PrimaryButton testid="dashboard-book-btn"><CalendarPlus size={16} /> Schedule a new visit</PrimaryButton></Link>
        </motion.div>

        {/* Next service callout */}
        {nextOne && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border border-[var(--border)] rounded-[20px] p-6 md:p-7 shadow-sm flex flex-wrap items-center gap-6 mb-8"
            data-testid="next-service-card"
          >
            <div className="flex-1 min-w-[240px]">
              <span className="text-[11px] uppercase tracking-[0.18em] font-semibold text-[var(--green)]">Next visit</span>
              <div className="font-serif text-[24px] md:text-[28px] text-[var(--green-dark)] leading-tight mt-1">
                {nextOne.service_label}{nextOne.tier_label ? <span className="italic-green"> — {nextOne.tier_label}</span> : null}
              </div>
              <div className="flex flex-wrap gap-4 mt-3 text-[13px] text-[var(--text-soft)]">
                <span className="inline-flex items-center gap-1.5"><Sparkles size={14} className="text-[var(--green)]" /> {nextOne.preferred_date} {nextOne.preferred_time && `· ${nextOne.preferred_time}`}</span>
                <span className="inline-flex items-center gap-1.5"><MapPin size={14} className="text-[var(--green)]" /> {nextOne.address}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[11px] uppercase tracking-[0.18em] font-semibold text-[var(--text-muted)]">Total</div>
              <div className="font-serif text-[32px] text-[var(--green-dark)] leading-none">${nextOne.grand_total}</div>
              <div className="mt-2 flex items-center gap-2 justify-end"><PayBadge b={nextOne} /></div>
            </div>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Calendar */}
          <div className="lg:col-span-3 bg-white border border-[var(--border)] rounded-[20px] p-5 md:p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-serif text-[20px] text-[var(--green-dark)]">Your calendar</h2>
              <span className="text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)]">Click a day to see details</span>
            </div>
            <MonthCalendar bookings={[...upcoming, ...past]} />
          </div>
          {/* Upcoming list */}
          <div className="lg:col-span-2 bg-white border border-[var(--border)] rounded-[20px] p-5 md:p-6 shadow-sm">
            <h2 className="font-serif text-[20px] text-[var(--green-dark)] mb-4">Upcoming services</h2>
            {loading && <div className="text-[13px] text-[var(--text-muted)]">Loading…</div>}
            {!loading && upcoming.length === 0 && (
              <div className="text-center py-8" data-testid="upcoming-empty">
                <div className="text-[40px]">🐾</div>
                <div className="text-[14px] text-[var(--text-muted)] mt-2">Nothing scheduled yet.</div>
                <Link to="/book" className="inline-block mt-4"><OutlineButton testid="empty-book">Schedule your first visit</OutlineButton></Link>
              </div>
            )}
            <ul className="space-y-3" data-testid="upcoming-list">
              {upcoming.map((b) => (
                <li key={b.id} className="upcoming-item" data-testid={`upcoming-${b.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="font-medium text-[14px] text-[var(--text)]">{b.service_label}{b.tier_label ? <span className="text-[var(--text-muted)]"> · {b.tier_label}</span> : null}</div>
                      <div className="text-[12px] text-[var(--text-muted)] mt-1 flex flex-wrap gap-x-3 gap-y-1">
                        <span className="inline-flex items-center gap-1"><Clock size={11} /> {b.preferred_date}{b.preferred_time && ` · ${b.preferred_time}`}</span>
                        <span>${b.grand_total}</span>
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        <StatusPill status={b.status} />
                        <PayBadge b={b} />
                      </div>
                    </div>
                    <button onClick={() => onCancel(b.id)} disabled={busyId === b.id} className="cancel-btn" data-testid={`cancel-${b.id}`} aria-label="Cancel booking">
                      <X size={14} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Past */}
        {past.length > 0 && (
          <div className="bg-white border border-[var(--border)] rounded-[20px] p-5 md:p-6 shadow-sm mt-6">
            <h2 className="font-serif text-[20px] text-[var(--green-dark)] mb-4">Past &amp; cancelled</h2>
            <ul className="divide-y divide-[var(--border)]" data-testid="past-list">
              {past.map((b) => (
                <li key={b.id} className="py-3 flex items-center justify-between gap-3 text-[13px]">
                  <div>
                    <span className="font-medium text-[var(--text)]">{b.service_label}</span>
                    {b.tier_label && <span className="text-[var(--text-muted)]"> · {b.tier_label}</span>}
                    <span className="text-[var(--text-muted)]"> · {b.preferred_date || b.created_at?.slice(0,10)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusPill status={b.status} />
                    <span className="text-[var(--text)]">${b.grand_total}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}
