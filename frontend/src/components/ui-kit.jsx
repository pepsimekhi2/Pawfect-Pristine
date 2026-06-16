import React from "react";
import { motion } from "framer-motion";

// SegmentedControl — refined editorial pill style
export function SegmentedControl({ options, value, onChange, testid = "segmented" }) {
  return (
    <div
      data-testid={testid}
      className="relative inline-flex bg-[var(--green-light)] p-1.5 rounded-full border border-[var(--border)] w-full max-w-md"
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            data-testid={`${testid}-${opt.value}`}
            onClick={() => onChange(opt.value)}
            className="relative z-10 flex-1 text-center py-2 px-4 font-medium cursor-pointer text-sm transition-colors"
            style={{ color: active ? "#fff" : "var(--text-soft)" }}
          >
            {active && (
              <motion.span
                layoutId={`${testid}-active`}
                className="absolute inset-0 rounded-full"
                style={{ background: "var(--green)", boxShadow: "0 4px 12px rgba(61,122,92,0.25)" }}
                transition={{ type: "spring", stiffness: 500, damping: 32 }}
              />
            )}
            <span className="relative z-10 inline-flex items-center gap-2 font-sans">
              <span>{opt.icon}</span> {opt.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

// PillToggle — soft border, green-selected
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
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => toggle(opt.value)}
            className="px-5 py-2.5 rounded-full font-medium cursor-pointer text-sm transition-all"
            style={{
              background: active ? "var(--green-light)" : "#fff",
              color: active ? "var(--green-mid)" : "var(--text-soft)",
              border: `1.5px solid ${active ? "var(--green)" : "var(--border-input)"}`,
            }}
          >
            <span className="inline-flex items-center gap-2">
              <span>{opt.icon}</span> {opt.label}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}

// Stepper — minimal circular buttons with serif numeric display
export function Stepper({ value, onChange, min = 0, max = 20, label, testid = "stepper" }) {
  const dec = () => onChange(Math.max(min, value - 1));
  const inc = () => onChange(Math.min(max, value + 1));
  return (
    <div className="flex items-center justify-between gap-4 w-full" data-testid={testid}>
      {label && <span className="text-[var(--text)] text-sm font-medium">{label}</span>}
      <div className="flex items-center gap-4">
        <motion.button
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.92 }}
          onClick={dec}
          disabled={value <= min}
          data-testid={`${testid}-dec`}
          className="w-10 h-10 flex items-center justify-center rounded-full border border-[var(--border-input)] bg-white text-[var(--green)] text-xl font-medium cursor-pointer disabled:opacity-30 hover:border-[var(--green)] transition-colors"
        >
          −
        </motion.button>
        <motion.span
          key={value}
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 350, damping: 20 }}
          className="font-serif text-2xl text-[var(--green-dark)] min-w-[2ch] text-center"
        >
          {value}
        </motion.span>
        <motion.button
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.92 }}
          onClick={inc}
          disabled={value >= max}
          data-testid={`${testid}-inc`}
          className="w-10 h-10 flex items-center justify-center rounded-full bg-[var(--green)] text-white text-xl font-medium cursor-pointer disabled:opacity-30 hover:bg-[var(--green-mid)] transition-colors"
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
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.15 }}
      className={`btn-primary ${className}`}
    >
      {children}
    </motion.button>
  );
}

export function OutlineButton({ children, onClick, testid, className = "" }) {
  return (
    <motion.button
      data-testid={testid}
      onClick={onClick}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.97 }}
      className={`btn-outline ${className}`}
    >
      {children}
    </motion.button>
  );
}

export function GhostWhiteButton({ children, onClick, testid, className = "" }) {
  return (
    <motion.button
      data-testid={testid}
      onClick={onClick}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.97 }}
      className={`btn-ghost ${className}`}
    >
      {children}
    </motion.button>
  );
}
