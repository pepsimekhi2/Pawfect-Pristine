import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LogOut, Phone, MapPin, MessageSquare, Send, Calendar as CalIcon,
  CheckCircle2, X, RefreshCw, Clock, Sparkles, Home, KeyRound, Lock, Bell, Users
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { PrimaryButton, OutlineButton } from "../components/ui-kit";
import { CalendarPicker, TimePicker } from "../components/CalendarPicker";

const ACCESS_LABELS = {
  home: "Customer home",
  lockbox: "Lockbox",
  hidden_key: "Hidden key",
  garage_code: "Garage code",
  doorman: "Doorman",
  other: "Other",
};
const ACCESS_ICONS = {
  home: <Home size={13} />, lockbox: <Lock size={13} />, hidden_key: <KeyRound size={13} />,
  garage_code: <KeyRound size={13} />, doorman: <Bell size={13} />, other: <KeyRound size={13} />,
};

function Stat({ label, value, accent }) {
  return (
    <div className="stat-card">
      <div className="text-[10.5px] uppercase tracking-[0.16em] font-semibold text-[var(--text-muted)]">{label}</div>
      <div className={`font-serif text-[28px] md:text-[32px] mt-1 leading-none ${accent ? "text-[var(--green)]" : "text-[var(--green-dark)]"}`}>{value}</div>
    </div>
  );
}

function StatusPill({ status }) {
  const s = status || "scheduled";
  return <span className={`status-pill status-${s}`}>{s.replace(/_/g, " ")}</span>;
}
function PayBadge({ b }) {
  const ps = b.payment_status || "unpaid";
  const label = { paid_full: "Paid in full", paid_half: "Half paid", unpaid: "Pay on arrival" }[ps] || ps;
  return <span className={`pay-pill pay-${ps}`}>{label}</span>;
}

export default function AdminPage() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [tab, setTab] = useState("today");
  const [bookings, setBookings] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState([]);
  const [active, setActive] = useState(null); // booking being acted on
  const [actionType, setActionType] = useState(null); // 'reschedule' | 'otw' | 'cancel'
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, today, up, cs] = await Promise.all([
        api.get("/api/admin/stats"),
        api.get("/api/admin/bookings/today"),
        api.get("/api/admin/bookings/upcoming"),
        api.get("/api/admin/customers"),
      ]);
      setStats(s.data);
      if (tab === "today") setBookings(today.data);
      else if (tab === "upcoming") setBookings(up.data);
      else if (tab === "customers") setBookings([]);
      setCustomers(cs.data);
      window.__pp_today = today.data;
      window.__pp_upcoming = up.data;
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    if (tab === "today" && window.__pp_today) setBookings(window.__pp_today);
    else if (tab === "upcoming" && window.__pp_upcoming) setBookings(window.__pp_upcoming);
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  const onLogout = async () => { await logout(); nav("/"); };

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3500); };

  const doNotify = async (b) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/api/admin/bookings/${b.id}/notify-otw`);
      if (data.sms_sent) {
        showToast(`SMS sent to ${b.phone} ✅`);
      } else {
        // Free SMS workaround: open the device's native Messages app with prefilled body.
        // On mobile (iOS/Android) this opens the SMS composer instantly.
        const a = document.createElement("a");
        a.href = data.sms_link;
        a.target = "_self";
        a.rel = "noopener noreferrer";
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast(`Opening Messages — just hit send ✉️`);
      }
      await load();
    } catch (e) {
      showToast("Couldn't notify. Try again.");
    } finally { setBusy(false); }
  };

  const doStatus = async (b, status) => {
    setBusy(true);
    try {
      await api.post(`/api/admin/bookings/${b.id}/status`, { status });
      showToast(`Marked as ${status.replace(/_/g, " ")}✅`);
      await load();
    } catch {
      showToast("Couldn't update status.");
    } finally { setBusy(false); }
  };

  const doCancel = async (b) => {
    if (!window.confirm(`Cancel ${b.name}'s ${b.service_label} on ${b.preferred_date}?`)) return;
    setBusy(true);
    try {
      await api.post(`/api/admin/bookings/${b.id}/cancel`);
      showToast("Booking cancelled.");
      await load();
    } catch {
      showToast("Couldn't cancel.");
    } finally { setBusy(false); }
  };

  const doReschedule = async (b, date, time) => {
    setBusy(true);
    try {
      await api.post(`/api/admin/bookings/${b.id}/reschedule`, { preferred_date: date, preferred_time: time });
      showToast("Rescheduled ✅");
      setActionType(null);
      setActive(null);
      await load();
    } catch (e) {
      showToast(e?.response?.data?.detail || "Couldn't reschedule.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-soft)]">
      {/* Top bar */}
      <header className="bg-[var(--green-dark)] text-white">
        <div className="max-w-7xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--green)]"><span className="text-lg">🐾</span></div>
            <div className="flex flex-col leading-tight">
              <span className="font-serif text-[17px] font-bold">Pawfect &amp; Pristine</span>
              <span className="text-[9.5px] uppercase tracking-[0.18em] font-medium text-[var(--green-pale)]">Admin Control · {user?.name}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={load} disabled={loading} className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-white/80 hover:text-white" data-testid="admin-refresh">
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
            <button onClick={onLogout} className="text-[13px] font-semibold text-white/80 hover:text-white inline-flex items-center gap-1.5" data-testid="admin-logout">
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 md:px-10 py-8 md:py-10">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8" data-testid="admin-stats">
          <Stat label="Today's bookings" value={stats?.today_bookings ?? "—"} accent />
          <Stat label="Today's revenue" value={stats ? `$${stats.today_revenue}` : "—"} />
          <Stat label="Upcoming bookings" value={stats?.upcoming_count ?? "—"} />
          <Stat label="Total customers" value={stats?.customers_count ?? "—"} />
        </div>

        {/* Tabs */}
        <div className="admin-tabs mb-5" data-testid="admin-tabs">
          {[
            { v: "today", label: "Today" },
            { v: "upcoming", label: "Upcoming" },
            { v: "customers", label: "Customers" },
          ].map((t) => (
            <button
              key={t.v}
              onClick={() => setTab(t.v)}
              data-testid={`admin-tab-${t.v}`}
              className={`admin-tab ${tab === t.v ? "is-active" : ""}`}
            >
              {t.label}
              {t.v === "today" && stats?.today_bookings ? <span className="tab-badge">{stats.today_bookings}</span> : null}
              {t.v === "upcoming" && stats?.upcoming_count ? <span className="tab-badge">{stats.upcoming_count}</span> : null}
              {t.v === "customers" && stats?.customers_count ? <span className="tab-badge">{stats.customers_count}</span> : null}
            </button>
          ))}
        </div>

        {/* Body */}
        {tab === "customers" ? (
          <CustomersTable customers={customers} />
        ) : (
          <BookingList
            bookings={bookings}
            loading={loading}
            onNotify={doNotify}
            onStatus={doStatus}
            onCancel={doCancel}
            onReschedule={(b) => { setActive(b); setActionType("reschedule"); }}
            busy={busy}
            emptyLabel={tab === "today" ? "Nothing on the books today. Enjoy the breather ☕" : "No upcoming bookings yet."}
          />
        )}
      </main>

      {/* Reschedule drawer */}
      <AnimatePresence>
        {actionType === "reschedule" && active && (
          <RescheduleModal
            booking={active}
            onClose={() => { setActionType(null); setActive(null); }}
            onSave={(d, t) => doReschedule(active, d, t)}
            busy={busy}
          />
        )}
      </AnimatePresence>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-[var(--green-dark)] text-white px-5 py-3 rounded-full shadow-lg text-[13px] font-medium z-50"
            data-testid="admin-toast"
          >{toast}</motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function BookingList({ bookings, loading, onNotify, onStatus, onCancel, onReschedule, busy, emptyLabel }) {
  if (loading) return <div className="text-[13px] text-[var(--text-muted)] py-12 text-center">Loading…</div>;
  if (!bookings.length) return (
    <div className="bg-white border border-[var(--border)] rounded-[20px] p-10 text-center" data-testid="admin-empty">
      <div className="text-[48px]">📅</div>
      <div className="text-[var(--text-muted)] text-[14px] mt-3">{emptyLabel}</div>
    </div>
  );
  return (
    <div className="space-y-3" data-testid="admin-bookings">
      {bookings.map((b) => <BookingCard key={b.id} b={b} onNotify={onNotify} onStatus={onStatus} onCancel={onCancel} onReschedule={onReschedule} busy={busy} />)}
    </div>
  );
}

function BookingCard({ b, onNotify, onStatus, onCancel, onReschedule, busy }) {
  const status = b.status || "scheduled";
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(b.address || "")}`;
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="booking-card" data-testid={`admin-booking-${b.id}`}>
      <div className="flex flex-wrap items-start gap-4">
        <div className="booking-time">
          <div className="text-[11px] uppercase tracking-[0.14em] font-semibold text-[var(--green)]">{b.preferred_date}</div>
          <div className="font-serif text-[28px] text-[var(--green-dark)] leading-none mt-1">{b.preferred_time || "—"}</div>
          <div className="mt-2"><StatusPill status={status} /></div>
        </div>
        <div className="flex-1 min-w-[220px]">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-semibold text-[16px] text-[var(--text)]">{b.name}</div>
            <a href={`tel:${b.phone}`} className="booking-link" data-testid={`admin-call-${b.id}`}><Phone size={12} /> {b.phone}</a>
            <a href={`sms:${b.phone}`} className="booking-link" data-testid={`admin-sms-${b.id}`}><MessageSquare size={12} /> SMS</a>
          </div>
          <a href={mapsUrl} target="_blank" rel="noreferrer" className="booking-link mt-1.5" data-testid={`admin-map-${b.id}`}>
            <MapPin size={12} /> {b.address}
          </a>
          <div className="mt-2 text-[13px] text-[var(--text)]">
            <span className="font-medium">{b.service_label}</span>
            {b.tier_label && <span className="text-[var(--text-muted)]"> · {b.tier_label}</span>}
            {b.pets > 0 && <span className="text-[var(--text-muted)]"> · {b.pets} {b.pets === 1 ? "pet" : "pets"}</span>}
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-2 text-[12px]">
            <span className="access-chip" title={b.access_notes || ""}>
              {ACCESS_ICONS[b.access_method] || ACCESS_ICONS.home}
              {ACCESS_LABELS[b.access_method] || "Customer home"}
            </span>
            <PayBadge b={b} />
            {b.eta && b.eta.distance_miles ? (
              <span className="text-[var(--text-muted)]">
                <Clock size={11} className="inline -mt-0.5 mr-1" />
                {b.eta.distance_miles} mi · {Math.round(b.eta.duration_minutes)} min
              </span>
            ) : null}
          </div>
          {b.access_notes && (
            <div className="access-notes" data-testid={`access-notes-${b.id}`}>
              <strong>Access:</strong> {b.access_notes}
            </div>
          )}
          {b.notes && (
            <div className="customer-notes" data-testid={`notes-${b.id}`}>
              <strong>Notes:</strong> {b.notes}
            </div>
          )}
        </div>
        <div className="booking-total">
          <div className="text-[10.5px] uppercase tracking-[0.14em] font-semibold text-[var(--text-muted)]">Total</div>
          <div className="font-serif text-[26px] text-[var(--green-dark)] leading-none mt-1">${b.grand_total}</div>
          <div className="text-[11px] text-[var(--text-muted)] mt-1">Due now ${b.due_now ?? 0}</div>
          <div className="text-[11px] text-[var(--text-muted)]">On arrival ${b.due_later ?? b.grand_total}</div>
        </div>
      </div>
      <div className="booking-actions" data-testid={`booking-actions-${b.id}`}>
        {status !== "cancelled" && status !== "completed" && (
          <>
            {status !== "on_the_way" && status !== "in_progress" && (
              <PrimaryButton testid={`otw-${b.id}`} onClick={() => onNotify(b)} disabled={busy}>
                <Send size={14} /> I'm on the way
              </PrimaryButton>
            )}
            {status === "on_the_way" && (
              <button onClick={() => onStatus(b, "in_progress")} disabled={busy} className="action-btn action-btn-go" data-testid={`arrived-${b.id}`}>
                <Sparkles size={14} /> Mark arrived
              </button>
            )}
            {status === "in_progress" && (
              <button onClick={() => onStatus(b, "completed")} disabled={busy} className="action-btn action-btn-go" data-testid={`complete-${b.id}`}>
                <CheckCircle2 size={14} /> Complete
              </button>
            )}
            <button onClick={() => onReschedule(b)} disabled={busy} className="action-btn" data-testid={`reschedule-${b.id}`}>
              <CalIcon size={14} /> Reschedule
            </button>
            <button onClick={() => onCancel(b)} disabled={busy} className="action-btn action-btn-danger" data-testid={`cancel-admin-${b.id}`}>
              <X size={14} /> Cancel
            </button>
          </>
        )}
        {(status === "completed" || status === "cancelled") && (
          <span className="text-[12px] text-[var(--text-muted)] italic">This booking is {status}.</span>
        )}
      </div>
    </motion.div>
  );
}

function RescheduleModal({ booking, onClose, onSave, busy }) {
  const [date, setDate] = useState(booking.preferred_date || "");
  const [time, setTime] = useState(booking.preferred_time || "");
  const [taken, setTaken] = useState([]);
  useEffect(() => {
    if (!date) return;
    const qs = new URLSearchParams({ date });
    if (booking.service_value) qs.set("service", booking.service_value);
    if (booking.tier_key) qs.set("tier", booking.tier_key);
    api.get(`/api/availability?${qs.toString()}`)
      .then((r) => {
        const slots = r.data?.slots || [];
        // Keep the booking's own current slot pickable
        setTaken(slots
          .filter((s) => (s.taken || s.too_late) && s.time !== booking.preferred_time)
          .map((s) => s.time));
      })
      .catch(() => setTaken([]));
  }, [date, booking.preferred_time, booking.service_value, booking.tier_key]);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="modal-backdrop" onClick={onClose}>
      <motion.div initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 24, opacity: 0 }} className="modal-card" onClick={(e) => e.stopPropagation()} data-testid="reschedule-modal">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <span className="eyebrow">Reschedule</span>
            <h3 className="font-serif text-[22px] text-[var(--green-dark)] mt-1 leading-tight">{booking.name} · {booking.service_label}</h3>
            <div className="text-[12px] text-[var(--text-muted)] mt-1">Currently {booking.preferred_date} at {booking.preferred_time}</div>
          </div>
          <button onClick={onClose} className="cancel-btn" data-testid="reschedule-close"><X size={14} /></button>
        </div>
        <CalendarPicker value={date} onChange={(d) => { setDate(d); setTime(""); }} testid="resched-cal" />
        <div className="text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)] mt-4 mb-2 font-semibold">New time</div>
        <TimePicker value={time} onChange={setTime} disabledTimes={taken} testid="resched-time" />
        <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-[var(--border)]">
          <OutlineButton testid="resched-cancel" onClick={onClose}>Cancel</OutlineButton>
          <PrimaryButton testid="resched-save" onClick={() => onSave(date, time)} disabled={busy || !date || !time}>
            {busy ? "Saving\u2026" : "Save reschedule"}
          </PrimaryButton>
        </div>
      </motion.div>
    </motion.div>
  );
}

function CustomersTable({ customers }) {
  if (!customers.length) return (
    <div className="bg-white border border-[var(--border)] rounded-[20px] p-10 text-center" data-testid="customers-empty">
      <Users className="mx-auto text-[var(--green-muted)]" size={48} />
      <div className="text-[var(--text-muted)] text-[14px] mt-3">No customers yet.</div>
    </div>
  );
  return (
    <div className="bg-white border border-[var(--border)] rounded-[20px] overflow-hidden" data-testid="customers-table">
      <div className="customers-header">
        <span>Name</span><span>Contact</span><span className="hidden md:inline">Joined</span><span className="text-right">Bookings</span>
      </div>
      {customers.map((c) => (
        <div key={c.id} className="customers-row" data-testid={`customer-${c.id}`}>
          <span className="font-medium text-[var(--text)]">{c.name}</span>
          <span className="text-[var(--text-muted)] flex flex-col">
            <a href={`mailto:${c.email}`} className="text-[12px] hover:text-[var(--green)]">{c.email}</a>
            {c.phone && <a href={`tel:${c.phone}`} className="text-[11px] hover:text-[var(--green)]">{c.phone}</a>}
          </span>
          <span className="text-[var(--text-muted)] text-[12px] hidden md:inline">{c.created_at?.slice(0, 10)}</span>
          <span className="text-right font-medium text-[var(--green-dark)]">{c.booking_count}</span>
        </div>
      ))}
    </div>
  );
}
