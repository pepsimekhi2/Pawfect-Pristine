import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DOW = ["S","M","T","W","T","F","S"];

function toIso(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function MonthCalendar({ bookings = [], onDayClick }) {
  const today = new Date(); today.setHours(0,0,0,0);
  const [viewMonth, setViewMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [activeIso, setActiveIso] = useState(null);

  const byDate = useMemo(() => {
    const map = new Map();
    for (const b of bookings) {
      if (!b.preferred_date) continue;
      const list = map.get(b.preferred_date) || [];
      list.push(b);
      map.set(b.preferred_date, list);
    }
    return map;
  }, [bookings]);

  const grid = useMemo(() => {
    const first = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1);
    const startDay = first.getDay();
    const daysInMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < startDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      cells.push(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), d));
    }
    while (cells.length % 7) cells.push(null);
    return cells;
  }, [viewMonth]);

  const activeBookings = activeIso ? byDate.get(activeIso) || [] : [];

  return (
    <div className="month-cal" data-testid="month-calendar">
      <div className="month-cal-head">
        <button onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1))} className="pp-cal-nav" aria-label="Previous month"><ChevronLeft size={18} /></button>
        <div className="font-serif text-[20px] md:text-[26px] text-[var(--green-dark)]">
          {MONTHS[viewMonth.getMonth()]} <span className="text-[var(--green-muted)]">{viewMonth.getFullYear()}</span>
        </div>
        <button onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1))} className="pp-cal-nav" aria-label="Next month"><ChevronRight size={18} /></button>
      </div>
      <div className="pp-cal-dow">
        {DOW.map((d, i) => <span key={i} className="pp-cal-dow-cell">{d}</span>)}
      </div>
      <motion.div
        key={`${viewMonth.getFullYear()}-${viewMonth.getMonth()}`}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className="month-cal-grid"
      >
        {grid.map((d, i) => {
          if (!d) return <span key={i} className="month-cal-cell is-empty" />;
          const iso = toIso(d);
          const list = byDate.get(iso) || [];
          const isToday = toIso(today) === iso;
          const isActive = activeIso === iso;
          return (
            <button
              type="button"
              key={iso}
              onClick={() => { setActiveIso(iso); onDayClick && onDayClick(iso, list); }}
              data-testid={`mcal-day-${iso}`}
              className={`month-cal-cell ${isToday ? "is-today" : ""} ${isActive ? "is-active" : ""} ${list.length ? "has-event" : ""}`}
            >
              <span className="day-num">{d.getDate()}</span>
              {list.length > 0 && (
                <div className="day-dots">
                  {list.slice(0, 3).map((b) => (
                    <span key={b.id} className={`day-dot ${b.status === "cancelled" ? "is-cancelled" : ""}`} />
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </motion.div>
      {activeIso && activeBookings.length > 0 && (
        <div className="month-cal-details" data-testid="mcal-details">
          <div className="text-[12px] uppercase tracking-[0.16em] font-semibold text-[var(--green)] mb-2">
            {new Date(activeIso + "T00:00:00").toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
          </div>
          <ul className="space-y-2">
            {activeBookings.map((b) => (
              <li key={b.id} className="flex items-center justify-between gap-3 text-[13px]">
                <span className="text-[var(--text)]">
                  <span className="font-medium">{b.service_label}</span>
                  {b.tier_label ? <span className="text-[var(--text-muted)]"> · {b.tier_label}</span> : null}
                  {b.preferred_time ? <span className="text-[var(--text-muted)]"> · {b.preferred_time}</span> : null}
                </span>
                <span className={`status-pill status-${b.status || "scheduled"}`}>{b.status || "scheduled"}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
