import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Clock, AlertTriangle, Phone, Sparkles } from "lucide-react";
import { PrimaryButton } from "./ui-kit";
import AddressAutocomplete from "./AddressAutocomplete";
import api from "../lib/api";

const zoneStyles = {
  standard: { bg: "var(--green-light)", border: "#c2dfc9", icon: "✓", iconColor: "var(--green)" },
  extended: { bg: "var(--warn-bg)", border: "var(--warn-border)", icon: "⚠", iconColor: "var(--warn-text)" },
  out_of_range: { bg: "#fdecea", border: "#f5b7b1", icon: "✕", iconColor: "#c0392b" },
};

export default function EtaCalculator() {
  const [address, setAddress] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!address.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const { data } = await api.post(`/api/eta`, { address: address.trim() });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const z = result ? zoneStyles[result.zone] : null;

  return (
    <section id="eta" className="py-20 md:py-28 px-6 md:px-12 bg-[var(--bg-soft)]">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-10">
          <span className="eyebrow"><Sparkles size={12} className="inline mr-1 -mt-0.5" />Live Drive ETA</span>
          <h2 className="font-serif text-3xl md:text-5xl font-bold mt-3 text-[var(--green-dark)] leading-tight tracking-tight">
            When would we <span className="italic-green">arrive today?</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-3 max-w-xl mx-auto text-[15px] leading-relaxed">
            Type your address — we&rsquo;ll calculate real driving time from Decatur and tell you which zone you&rsquo;re in.
          </p>
        </div>

        <div className="bg-white border border-[var(--border)] rounded-[20px] p-6 md:p-10 shadow-sm">
          <form onSubmit={submit} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <AddressAutocomplete
                value={address}
                onChange={setAddress}
                verifyOnBlur={false}
                placeholder="e.g. 1280 W Peachtree St, Atlanta, GA"
                testid="eta-autocomplete"
              />
            </div>
            <PrimaryButton testid="eta-submit" type="submit" disabled={loading || !address.trim()}>
              {loading ? "Routing…" : "Get my ETA"}
            </PrimaryButton>
          </form>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                data-testid="eta-error"
                className="mt-5 p-4 rounded-xl border border-[#f5b7b1] bg-[#fdecea] font-medium text-[#c0392b] flex items-center gap-3 text-sm"
              >
                <AlertTriangle size={18} /> {error}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {result && z && (
              <motion.div
                key={result.address}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                data-testid="eta-result"
                className="mt-6"
              >
                <div className="grid md:grid-cols-3 gap-4">
                  <Stat icon={<MapPin size={18} />} label="Distance" value={`${result.distance_miles} mi`} testid="eta-distance" />
                  <Stat icon={<Clock size={18} />} label="Drive time" value={`~${Math.round(result.duration_minutes)} min`} testid="eta-duration" />
                  <Stat icon={<span className="text-base">⏰</span>} label="Arrive by" value={result.arrival_window} testid="eta-arrival" />
                </div>

                <div className="mt-5 p-5 md:p-6 rounded-2xl border" style={{ background: z.bg, borderColor: z.border }}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">Service Zone</div>
                      <div className="font-serif text-2xl md:text-3xl text-[var(--green-dark)] mt-1" data-testid="eta-zone-label">
                        <span className="mr-2" style={{ color: z.iconColor }}>{z.icon}</span>
                        {result.zone_label}
                      </div>
                    </div>
                    {result.extra_fee > 0 && (
                      <span className="tag tag-pet" data-testid="eta-fee">+${result.extra_fee} travel fee</span>
                    )}
                    {result.zone === "out_of_range" && (
                      <a href="tel:+14047503446" data-testid="eta-call" className="btn-primary" style={{ padding: "10px 22px", fontSize: 13 }}>
                        <Phone size={14} /> Call (404) 750-3446
                      </a>
                    )}
                  </div>
                  <p className="mt-3 text-[var(--text-soft)] text-[14px] leading-relaxed" data-testid="eta-zone-message">{result.zone_message}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

function Stat({ icon, label, value, testid }) {
  return (
    <div className="bg-[var(--green-light)] border border-[#c2dfc9] rounded-xl p-5" data-testid={testid}>
      <div className="flex items-center gap-2 text-[var(--green-mid)] font-medium text-[11px] uppercase tracking-[0.16em]">
        {icon} {label}
      </div>
      <div className="font-serif text-2xl md:text-[28px] text-[var(--green-dark)] mt-1.5 leading-tight">{value}</div>
    </div>
  );
}
