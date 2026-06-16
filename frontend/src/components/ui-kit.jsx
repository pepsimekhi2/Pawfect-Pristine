import React from "react";
import { motion } from "framer-motion";

export function SegmentedControl({ options, value, onChange, testid = "segmented" }) {
  return (
    <div
      data-testid={testid}
      className="relative flex bg-[var(--pp-bg)] p-1.5 rounded-full border-2 border-ink shadow-pop-sm w-full max-w-md"
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            data-testid={`${testid}-${opt.value}`}
            onClick={() => onChange(opt.value)}
            className="relative z-10 flex-1 text-center py-2.5 px-4 font-extrabold cursor-pointer text-sm md:text-base"
            style={{ color: active ? "#2D2424" : "#5C4E4E" }}
          >
            {active && (
              <motion.span
                layoutId={`${testid}-active`}
                className="absolute inset-0 rounded-full border-2 border-ink"
                style={{ background: "var(--pp-pink)", boxShadow: "2px 2px 0 0 var(--pp-ink)" }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
            <span className="relative z-10 inline-flex items-center gap-2">
              {opt.icon} {opt.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function PillToggle({ options, value, onChange, multi = false, testid = "pills" }) {
  const isActive = (v) => (multi ? value?.includes(v) : value === v);
  const toggle = (v) => {
    if (multi) {
      const set = new Set(value || []);
      set.has(v) ? set.delete(v) : set.add(v);
      onChange([...set]);
    } else {
      onChange(v);
    }
  };
  return (
    <div className="flex flex-wrap gap-2.5" data-testid={testid}>
      {options.map((opt) => {
        const active = isActive(opt.value);
        return (
          <motion.button
            key={opt.value}
            data-testid={`${testid}-${opt.value}`}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => toggle(opt.value)}
            className="px-5 py-2.5 rounded-full border-2 border-ink font-bold cursor-pointer text-sm md:text-base transition-colors"
            style={{
              background: active ? "var(--pp-terracotta)" : "#fff",
              color: active ? "#fff" : "var(--pp-ink)",
              boxShadow: active ? "3px 3px 0 0 var(--pp-ink)" : "2px 2px 0 0 var(--pp-ink)",
            }}
          >
            <span className="inline-flex items-center gap-2">
              {opt.icon} {opt.label}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}

export function Stepper({ value, onChange, min = 0, max = 20, label, testid = "stepper" }) {
  const dec = () => onChange(Math.max(min, value - 1));
  const inc = () => onChange(Math.min(max, value + 1));
  return (
    <div className="flex items-center justify-between gap-4 w-full" data-testid={testid}>
      {label && <span className="font-bold text-[var(--pp-ink)] text-base md:text-lg">{label}</span>}
      <div className="flex items-center gap-4">
        <motion.button
          whileHover={{ scale: 1.1, rotate: -5 }}
          whileTap={{ scale: 0.9 }}
          onClick={dec}
          disabled={value <= min}
          data-testid={`${testid}-dec`}
          className="w-11 h-11 flex items-center justify-center rounded-full border-2 border-ink bg-white text-2xl font-black shadow-pop-sm cursor-pointer disabled:opacity-40"
        >
          −
        </motion.button>
        <motion.span
          key={value}
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="font-heading font-black text-3xl text-[var(--pp-ink)] min-w-[2ch] text-center"
        >
          {value}
        </motion.span>
        <motion.button
          whileHover={{ scale: 1.1, rotate: 5 }}
          whileTap={{ scale: 0.9 }}
          onClick={inc}
          disabled={value >= max}
          data-testid={`${testid}-inc`}
          className="w-11 h-11 flex items-center justify-center rounded-full border-2 border-ink bg-[var(--pp-sage)] text-white text-2xl font-black shadow-pop-sm cursor-pointer disabled:opacity-40"
        >
          +
        </motion.button>
      </div>
    </div>
  );
}

export function PrimaryButton({ children, onClick, testid, disabled, type = "button", className = "" }) {
  return (
    <motion.button
      type={type}
      data-testid={testid}
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: 1.04, y: -2 }}
      whileTap={{ scale: 0.96, y: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      className={`inline-flex items-center justify-center gap-2 bg-[var(--pp-terracotta)] text-white font-heading font-extrabold px-7 py-3.5 rounded-full border-2 border-ink shadow-pop hover:shadow-pop-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-base md:text-lg ${className}`}
    >
      {children}
    </motion.button>
  );
}

export function GhostButton({ children, onClick, testid, className = "" }) {
  return (
    <motion.button
      data-testid={testid}
      onClick={onClick}
      whileHover={{ scale: 1.04, y: -2 }}
      whileTap={{ scale: 0.96 }}
      className={`inline-flex items-center gap-2 bg-white text-[var(--pp-ink)] font-heading font-extrabold px-6 py-3 rounded-full border-2 border-ink shadow-pop-sm hover:shadow-pop cursor-pointer ${className}`}
    >
      {children}
    </motion.button>
  );
}

export function PawSVG({ size = 24, color = "#2D2424", className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className} aria-hidden="true">
      <ellipse cx="14" cy="22" rx="6" ry="8" fill={color} />
      <ellipse cx="32" cy="14" rx="6" ry="8" fill={color} />
      <ellipse cx="50" cy="22" rx="6" ry="8" fill={color} />
      <ellipse cx="22" cy="34" rx="5" ry="7" fill={color} />
      <ellipse cx="42" cy="34" rx="5" ry="7" fill={color} />
      <path d="M32 30c-9 0-16 8-16 16 0 6 5 10 11 10 2 0 3-1 5-1s3 1 5 1c6 0 11-4 11-10 0-8-7-16-16-16z" fill={color} />
    </svg>
  );
}
