import React, { useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, CheckCircle2, Send } from "lucide-react";
import { SegmentedControl, PillToggle, Stepper, PrimaryButton, GhostButton } from "./ui-kit";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const HOME_SERVICES = [
  { value: "general_cleaning", label: "General Cleaning", icon: "🧹" },
  { value: "deep_cleaning", label: "Deep Cleaning", icon: "✨" },
  { value: "organizing", label: "Organizing", icon: "📦" },
  { value: "garage_shed", label: "Garages & Sheds", icon: "🏠" },
];
const PET_SERVICES = [
  { value: "dog_walking", label: "Dog Walking", icon: "🐕" },
  { value: "pet_sitting", label: "Pet Sitting", icon: "🐱" },
  { value: "feeding_care", label: "Feeding & Care", icon: "🍽️" },
  { value: "playtime", label: "Playtime & Enrichment", icon: "🎾" },
];

const colors = ["#E06D53", "#89A894", "#F4C770", "#F2D8C9", "#FAD3CB", "#D8E6DE"];

function fireConfetti() {
  const pieces = 60;
  for (let i = 0; i < pieces; i++) {
    const el = document.createElement("div");
    el.className = "confetti-piece";
    el.style.left = `${Math.random() * 100}vw`;
    el.style.background = colors[i % colors.length];
    el.style.setProperty("--x", `${(Math.random() - 0.5) * 200}px`);
    el.style.animationDelay = `${Math.random() * 0.4}s`;
    el.style.transform = `rotate(${Math.random() * 360}deg)`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }
}

export default function BookingForm() {
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState("home");
  const [service, setService] = useState("general_cleaning");
  const [pets, setPets] = useState(0);
  const [bedrooms, setBedrooms] = useState(2);
  const [bathrooms, setBathrooms] = useState(1);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState("");

  const services = category === "home" ? HOME_SERVICES : PET_SERVICES;

  const handleCategory = (cat) => {
    setCategory(cat);
    setService(cat === "home" ? "general_cleaning" : "dog_walking");
  };

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const { data } = await axios.post(`${API}/bookings`, {
        name, phone, address,
        service_category: category,
        service_type: services.find((s) => s.value === service)?.label || service,
        pets, bedrooms, bathrooms,
        notes,
        preferred_date: date,
        preferred_time: time,
      });
      setSuccess(data);
      fireConfetti();
      setStep(4);
    } catch (err) {
      setError(err?.response?.data?.detail || "Couldn't submit. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const next = () => setStep((s) => Math.min(3, s + 1));
  const back = () => setStep((s) => Math.max(1, s - 1));

  const step1Valid = category && service;
  const step2Valid = category === "home" ? bedrooms >= 0 : pets >= 0;
  const step3Valid = name.trim() && phone.trim() && address.trim();

  return (
    <section id="book" className="py-20 md:py-28 px-6 md:px-12 lg:px-24">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <span className="sticker"><Sparkles size={14} /> Book a visit</span>
          <h2 className="font-heading text-4xl md:text-6xl font-black mt-4 leading-[1.02] tracking-tight">
            Let&rsquo;s get you <span className="squiggle-underline">booked.</span>
          </h2>
          <p className="text-[var(--pp-ink-soft)] mt-3 font-semibold text-lg">
            Four playful steps. No contracts. We&rsquo;ll text you back fast.
          </p>
        </div>

        <div className="rounded-[32px] border-2 border-ink bg-white shadow-pop-lg p-6 md:p-10">
          {step < 4 && <StepDots step={step} total={3} />}

          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="s1" {...fade} className="space-y-7">
                <FieldLabel>Are we cleaning a home or caring for a pet?</FieldLabel>
                <SegmentedControl
                  testid="cat-segmented"
                  value={category}
                  onChange={handleCategory}
                  options={[
                    { value: "home", label: "Home", icon: "🏡" },
                    { value: "pet", label: "Pet", icon: "🐾" },
                  ]}
                />
                <FieldLabel>Pick a service</FieldLabel>
                <PillToggle testid="service-pills" options={services} value={service} onChange={setService} />
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="s2" {...fade} className="space-y-7">
                {category === "home" ? (
                  <>
                    <FieldLabel>How big is the space?</FieldLabel>
                    <Stepper testid="bed-stepper" label="Bedrooms" value={bedrooms} onChange={setBedrooms} min={0} max={10} />
                    <Stepper testid="bath-stepper" label="Bathrooms" value={bathrooms} onChange={setBathrooms} min={0} max={10} />
                    <Stepper testid="pet-home-stepper" label="Pets in the home" value={pets} onChange={setPets} min={0} max={10} />
                  </>
                ) : (
                  <>
                    <FieldLabel>Tell us about your crew</FieldLabel>
                    <Stepper testid="pet-stepper" label="Number of pets" value={pets} onChange={setPets} min={1} max={10} />
                  </>
                )}
                <div>
                  <FieldLabel>Anything we should know?</FieldLabel>
                  <textarea
                    data-testid="notes-input"
                    className="pp-input"
                    placeholder="Skittish cat, allergies, gate code, etc."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="s3" {...fade} className="space-y-5">
                <FieldLabel>Your details</FieldLabel>
                <div className="grid md:grid-cols-2 gap-4">
                  <input className="pp-input" placeholder="Your name" data-testid="name-input" value={name} onChange={(e) => setName(e.target.value)} />
                  <input className="pp-input" placeholder="Phone (e.g. 404-555-0123)" data-testid="phone-input" value={phone} onChange={(e) => setPhone(e.target.value)} />
                </div>
                <input className="pp-input" placeholder="Service address" data-testid="address-input" value={address} onChange={(e) => setAddress(e.target.value)} />
                <div className="grid md:grid-cols-2 gap-4">
                  <input className="pp-input" placeholder="Preferred date (e.g. Sat Jan 18)" data-testid="date-input" value={date} onChange={(e) => setDate(e.target.value)} />
                  <input className="pp-input" placeholder="Preferred time (e.g. 2pm)" data-testid="time-input" value={time} onChange={(e) => setTime(e.target.value)} />
                </div>
                {error && <div className="p-3 rounded-xl border-2 border-ink bg-[var(--pp-terracotta-light)] font-bold" data-testid="form-error">{error}</div>}
              </motion.div>
            )}

            {step === 4 && success && (
              <motion.div
                key="s4"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 250, damping: 16 }}
                className="text-center py-6"
                data-testid="booking-success"
              >
                <motion.div
                  animate={{ rotate: [0, -10, 10, -8, 8, 0] }}
                  transition={{ duration: 0.9 }}
                  className="inline-block"
                >
                  <CheckCircle2 size={96} className="text-[var(--pp-sage)]" strokeWidth={2.5} />
                </motion.div>
                <h3 className="font-heading text-4xl md:text-5xl font-black mt-4">You&rsquo;re in! 🎉</h3>
                <p className="text-[var(--pp-ink-soft)] mt-3 font-semibold text-lg max-w-md mx-auto">
                  Thanks, {name}! {success.sms_sent ? "We just texted the team — expect a reply in minutes." : "We've logged your request and will reach out shortly."}
                </p>
                {success.eta && (
                  <div className="inline-flex flex-wrap items-center justify-center gap-2 mt-5">
                    <span className="sticker" style={{ background: "var(--pp-sage-light)" }}>{success.eta.distance_miles} mi away</span>
                    <span className="sticker" style={{ background: "var(--pp-pink)" }}>~{Math.round(success.eta.duration_minutes)} min drive</span>
                    {success.eta.extra_fee > 0 && (
                      <span className="sticker" style={{ background: "var(--pp-yellow)" }}>+${success.eta.extra_fee} travel</span>
                    )}
                  </div>
                )}
                <div className="mt-7">
                  <GhostButton testid="book-another" onClick={() => { setStep(1); setSuccess(null); setName(""); setPhone(""); setAddress(""); setNotes(""); setDate(""); setTime(""); }}>
                    Book another visit
                  </GhostButton>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {step < 4 && (
            <div className="flex items-center justify-between mt-9 pt-6 border-t-2 border-dashed border-ink/20">
              {step > 1 ? (
                <GhostButton testid="back-btn" onClick={back}>← Back</GhostButton>
              ) : <span />}
              {step < 3 ? (
                <PrimaryButton
                  testid="next-btn"
                  onClick={next}
                  disabled={(step === 1 && !step1Valid) || (step === 2 && !step2Valid)}
                >
                  Next →
                </PrimaryButton>
              ) : (
                <PrimaryButton testid="submit-btn" onClick={submit} disabled={!step3Valid || submitting}>
                  {submitting ? "Sending…" : (<><Send size={18} /> Send booking</>)}
                </PrimaryButton>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

const fade = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
  transition: { type: "spring", stiffness: 250, damping: 24 },
};

function FieldLabel({ children }) {
  return <div className="font-heading font-extrabold text-xl md:text-2xl text-[var(--pp-ink)] leading-tight">{children}</div>;
}

function StepDots({ step, total }) {
  return (
    <div className="flex items-center gap-3 mb-7" data-testid="step-dots">
      {Array.from({ length: total }).map((_, i) => {
        const idx = i + 1;
        const active = idx <= step;
        return (
          <motion.div
            key={i}
            animate={{ scale: idx === step ? 1.2 : 1 }}
            className="h-3 rounded-full border-2 border-ink"
            style={{
              width: idx === step ? 40 : 14,
              background: active ? "var(--pp-terracotta)" : "#fff",
              boxShadow: active ? "2px 2px 0 0 var(--pp-ink)" : "none",
            }}
          />
        );
      })}
      <span className="ml-auto font-extrabold text-sm text-[var(--pp-muted)] uppercase tracking-wider">Step {step} of {total}</span>
    </div>
  );
}
