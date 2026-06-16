import React, { useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Clock, AlertTriangle, Phone, Sparkles } from "lucide-react";
import { PrimaryButton, PawSVG } from "./ui-kit";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const zoneStyles = {
  standard: { bg: "var(--pp-sage-light)", border: "#2D2424", emoji: "🎉" },
  extended: { bg: "var(--pp-yellow)", border: "#2D2424", emoji: "🚗" },
  out_of_range: { bg: "var(--pp-terracotta-light)", border: "#2D2424", emoji: "📞" },
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
      const { data } = await axios.post(`${API}/eta`, { address: address.trim() });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const z = result ? zoneStyles[result.zone] : null;

  return (
    <section id="eta" className="relative py-20 md:py-28 px-6 md:px-12 lg:px-24">
      <div className="absolute -top-6 left-10 float-paw" style={{ "--rot": "-18deg" }}>
        <PawSVG size={42} color="#E06D53" />
      </div>
      <div className="absolute top-32 right-10 float-paw" style={{ "--rot": "22deg", animationDelay: "1s" }}>
        <PawSVG size={36} color="#89A894" />
      </div>

      <div
        className="max-w-5xl mx-auto rounded-[36px] border-2 border-ink shadow-pop-lg p-8 md:p-12"
        style={{ background: "var(--pp-sage-light)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-8">
          <div>
            <span className="sticker"><Sparkles size={14} /> Live Drive ETA</span>
            <h2 className="font-heading text-4xl md:text-5xl font-black mt-4 leading-[1.05] tracking-tight">
              When would we <span className="squiggle-underline">arrive today?</span>
            </h2>
            <p className="text-[var(--pp-ink-soft)] mt-3 max-w-md text-base md:text-lg font-semibold">
              Type your address — we&rsquo;ll calculate real driving time from Decatur and tell you which zone you&rsquo;re in.
            </p>
          </div>
        </div>

        <form onSubmit={submit} className="flex flex-col sm:flex-row gap-3">
          <input
            data-testid="eta-input"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="e.g. 1280 W Peachtree St, Atlanta, GA"
            className="pp-input flex-1"
          />
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
              className="mt-5 p-4 rounded-2xl border-2 border-ink bg-white font-bold flex items-center gap-3"
            >
              <AlertTriangle size={20} className="text-[var(--pp-terracotta)]" /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {result && (
            <motion.div
              key={result.address}
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ type: "spring", stiffness: 320, damping: 22 }}
              data-testid="eta-result"
              className="mt-7 rounded-3xl border-2 border-ink p-6 md:p-8"
              style={{ background: z.bg, boxShadow: "5px 5px 0 0 var(--pp-ink)" }}
            >
              <div className="grid md:grid-cols-3 gap-5 md:gap-7">
                <Stat icon={<MapPin size={22} />} label="Distance" value={`${result.distance_miles} mi`} testid="eta-distance" />
                <Stat icon={<Clock size={22} />} label="Drive time" value={`~${Math.round(result.duration_minutes)} min`} testid="eta-duration" />
                <Stat icon={<span className="text-2xl">{z.emoji}</span>} label="Arrive by" value={result.arrival_window} testid="eta-arrival" />
              </div>

              <div className="mt-6 p-4 md:p-5 rounded-2xl bg-white border-2 border-ink">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-extrabold uppercase tracking-wider text-[var(--pp-muted)]">Zone</div>
                    <div className="font-heading font-black text-2xl md:text-3xl" data-testid="eta-zone-label">{result.zone_label}</div>
                  </div>
                  {result.extra_fee > 0 && (
                    <span className="sticker" style={{ background: "var(--pp-yellow)" }} data-testid="eta-fee">
                      +${result.extra_fee} travel fee
                    </span>
                  )}
                  {result.zone === "out_of_range" && (
                    <a href="tel:+14703814682" data-testid="eta-call" className="sticker hover:scale-105 transition-transform" style={{ background: "var(--pp-terracotta)", color: "#fff" }}>
                      <Phone size={14} /> Call (470) 381-4682
                    </a>
                  )}
                </div>
                <p className="mt-3 font-semibold text-[var(--pp-ink-soft)]" data-testid="eta-zone-message">{result.zone_message}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

function Stat({ icon, label, value, testid }) {
  return (
    <div className="bg-white border-2 border-ink rounded-2xl p-5 shadow-pop-sm" data-testid={testid}>
      <div className="flex items-center gap-2 text-[var(--pp-muted)] font-extrabold uppercase tracking-wider text-xs">
        {icon} {label}
      </div>
      <div className="font-heading font-black text-2xl md:text-3xl mt-2 leading-none">{value}</div>
    </div>
  );
}
