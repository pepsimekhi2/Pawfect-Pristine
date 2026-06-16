import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Calendar as CalIcon } from "lucide-react";

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DOW = ["S","M","T","W","T","F","S"];

function toIso(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function parseIso(s) {
  if (!s) return null;
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function CalendarPicker({ value, onChange, minDate, markedDates = [], testid = "calendar" }) {
  const today = new Date(); today.setHours(0,0,0,0);
  const min = minDate ? new Date(minDate) : today;
  min.setHours(0,0,0,0);
  const selected = parseIso(value);
  const [viewMonth, setViewMonth] = useState(() => {
    const base = selected || today;
    return new Date(base.getFullYear(), base.getMonth(), 1);
  });

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

  const prev = () => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1));
  const next = () => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1));
  const marks = new Set(markedDates);

  return (
    <div className="pp-calendar" data-testid={testid}>
      <div className="pp-cal-head">
        <button type="button" onClick={prev} className="pp-cal-nav" data-testid={`${testid}-prev`} aria-label="Previous month">
          <ChevronLeft size={18} />
        </button>
        <div className="pp-cal-title font-serif">
          {MONTHS[viewMonth.getMonth()]} <span className="pp-cal-year">{viewMonth.getFullYear()}</span>
        </div>
        <button type="button" onClick={next} className="pp-cal-nav" data-testid={`${testid}-next`} aria-label="Next month">
          <ChevronRight size={18} />
        </button>
      </div>
      <div className="pp-cal-dow">
        {DOW.map((d, i) => <span key={i} className="pp-cal-dow-cell">{d}</span>)}
      </div>
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.div
          key={`${viewMonth.getFullYear()}-${viewMonth.getMonth()}`}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.18 }}
          className="pp-cal-grid"
        >
          {grid.map((d, i) => {
            if (!d) return <span key={i} className="pp-cal-cell pp-cal-empty" />;
            const iso = toIso(d);
            const isSelected = selected && toIso(selected) === iso;
            const isPast = d < min;
            const marked = marks.has(iso);
            const isToday = toIso(today) === iso;
            return (
              <button
                type="button"
                key={iso}
                disabled={isPast}
                onClick={() => onChange(iso)}
                data-testid={`${testid}-day-${iso}`}
                className={`pp-cal-cell ${isSelected ? "is-selected" : ""} ${isPast ? "is-past" : ""} ${isToday ? "is-today" : ""}`}
              >
                <span>{d.getDate()}</span>
                {marked && !isSelected && <span className="pp-cal-dot" />}
              </button>
            );
          })}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

const HOURS = [
  "08:00","08:30","09:00","09:30","10:00","10:30",
  "11:00","11:30","12:00","12:30","13:00","13:30",
  "14:00","14:30","15:00","15:30","16:00","16:30",
  "17:00","17:30","18:00","18:30","19:00",
];
function prettyTime(t) {
  const [h, m] = t.split(":").map(Number);
  const suf = h >= 12 ? "PM" : "AM";
  const hh = ((h + 11) % 12) + 1;
  return `${hh}:${String(m).padStart(2, "0")} ${suf}`;
}
export function TimePicker({ value, onChange, testid = "time-picker" }) {
  return (
    <div className="pp-time-grid" data-testid={testid}>
      {HOURS.map((t) => (
        <button
          type="button"
          key={t}
          onClick={() => onChange(t)}
          data-testid={`${testid}-${t}`}
          className={`pp-time-cell ${value === t ? "is-selected" : ""}`}
        >
          {prettyTime(t)}
        </button>
      ))}
    </div>
  );
}

export { toIso, parseIso };
export function FormattedDate({ iso }) {
  if (!iso) return null;
  const d = parseIso(iso);
  if (!d) return iso;
  return (
    <span className="inline-flex items-center gap-1.5 text-[var(--green-dark)] font-medium">
      <CalIcon size={14} /> {d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" })}
    </span>
  );
}
