import React, { useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, CheckCircle2, Send } from "lucide-react";
import { SegmentedControl, PillToggle, Stepper, PrimaryButton, OutlineButton } from "./ui-kit";

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

const confettiColors = ["#3d7a5c", "#7a9e8a", "#a8cfc0", "#d4a435", "#eef7f2"];

function fireConfetti() {
  const pieces = 45;
  for (let i = 0; i < pieces; i++) {
    const el = document.createElement("div");
    el.className = "confetti-piece";
    el.style.left = `${Math.random() * 100}vw`;
    el.style.background = confettiColors[i % confettiColors.length];
    el.style.setProperty("--x", `${(Math.random() - 0.5) * 200}px`);
    el.style.animationDelay = `${Math.random() * 0.4}s`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3200);
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
    if (cat === "pet" && pets < 1) setPets(1);
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
  const step3Valid = name.trim() && phone.trim() && address.trim();

  return (
    <section id="book" className="py-20 md:py-28 px-6 md:px-12">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <span className="eyebrow"><Sparkles size={12} className="inline mr-1 -mt-0.5" />Book a visit</span>
          <h2 className="font-serif text-3xl md:text-5xl font-bold mt-3 text-[var(--green-dark)] leading-tight tracking-tight">
            Let&rsquo;s get you <span className="italic-green">booked.</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-3 text-[15px] leading-relaxed max-w-md mx-auto">
            Three quick steps. No contracts. We&rsquo;ll text you back fast.
          </p>
        </div>

        <div className="bg-white border border-[var(--border)] rounded-[20px] shadow-sm p-6 md:p-10">
          {step < 4 && <ProgressBar step={step} total={3} />}

          <AnimatePresence initial={false}>
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
              <motion.div key="s2" {...fade} className="space-y-6">
                {category === "home" ? (
                  <>
                    <FieldLabel>How big is the space?</FieldLabel>
                    <Stepper testid="bed-stepper" label="Bedrooms" value={bedrooms} onChange={setBedrooms} min={0} max={10} />
                    <div className="h-px bg-[var(--border)]" />
                    <Stepper testid="bath-stepper" label="Bathrooms" value={bathrooms} onChange={setBathrooms} min={0} max={10} />
                    <div className="h-px bg-[var(--border)]" />
                    <Stepper testid="pet-home-stepper" label="Pets in the home" value={pets} onChange={setPets} min={0} max={10} />
                  </>
                ) : (
                  <>
                    <FieldLabel>Tell us about your crew</FieldLabel>
                    <Stepper testid="pet-stepper" label="Number of pets" value={pets} onChange={setPets} min={1} max={10} />
                  </>
                )}
                <div className="pt-2">
                  <FieldLabel>Anything we should know?</FieldLabel>
                  <textarea
                    data-testid="notes-input"
                    className="pp-input mt-3"
                    placeholder="Skittish cat, allergies, gate code, etc."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="s3" {...fade} className="space-y-4">
                <FieldLabel>Your details</FieldLabel>
                <div className="grid md:grid-cols-2 gap-3">
                  <div>
                    <SmallLabel>Name</SmallLabel>
                    <input className="pp-input mt-1.5" placeholder="Your full name" data-testid="name-input" value={name} onChange={(e) => setName(e.target.value)} />
                  </div>
                  <div>
                    <SmallLabel>Phone</SmallLabel>
                    <input className="pp-input mt-1.5" placeholder="(404) 555-0123" data-testid="phone-input" value={phone} onChange={(e) => setPhone(e.target.value)} />
                  </div>
                </div>
                <div>
                  <SmallLabel>Service address</SmallLabel>
                  <input className="pp-input mt-1.5" placeholder="Street, City, State ZIP" data-testid="address-input" value={address} onChange={(e) => setAddress(e.target.value)} />
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  <div>
                    <SmallLabel>Preferred date</SmallLabel>
                    <input className="pp-input mt-1.5" placeholder="e.g. Sat, Jan 18" data-testid="date-input" value={date} onChange={(e) => setDate(e.target.value)} />
                  </div>
                  <div>
                    <SmallLabel>Preferred time</SmallLabel>
                    <input className="pp-input mt-1.5" placeholder="e.g. 2pm" data-testid="time-input" value={time} onChange={(e) => setTime(e.target.value)} />
                  </div>
                </div>
                {error && <div className="p-3 rounded-lg border border-[#f5b7b1] bg-[#fdecea] text-[#c0392b] font-medium text-sm" data-testid="form-error">{error}</div>}
              </motion.div>
            )}

            {step === 4 && success && (
              <motion.div
                key="s4"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                className="text-center py-6"
                data-testid="booking-success"
              >
                <motion.div
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }}
                  className="inline-block"
                >
                  <CheckCircle2 size={80} className="text-[var(--green)]" strokeWidth={1.5} />
                </motion.div>
                <h3 className="font-serif text-3xl md:text-4xl text-[var(--green-dark)] mt-5">
                  You&rsquo;re <span className="italic-green">booked.</span>
                </h3>
                <p className="text-[var(--text-muted)] mt-3 text-[15px] leading-relaxed max-w-md mx-auto">
                  Thanks, {name}. {success.sms_sent ? "We just texted the team — expect a reply in minutes." : "We\u2019ve logged your request and will reach out shortly."}
                </p>
                {success.eta && (
                  <div className="inline-flex flex-wrap items-center justify-center gap-2 mt-5">
                    <span className="tag tag-home">{success.eta.distance_miles} mi away</span>
                    <span className="tag tag-home">~{Math.round(success.eta.duration_minutes)} min drive</span>
                    {success.eta.extra_fee > 0 && (
                      <span className="tag tag-pet">+${success.eta.extra_fee} travel</span>
                    )}
                  </div>
                )}
                <div className="mt-7">
                  <OutlineButton testid="book-another" onClick={() => { setStep(1); setSuccess(null); setName(""); setPhone(""); setAddress(""); setNotes(""); setDate(""); setTime(""); }}>
                    Book another visit
                  </OutlineButton>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {step < 4 && (
            <div className="flex items-center justify-between mt-9 pt-6 border-t border-[var(--border)]">
              {step > 1 ? (
                <OutlineButton testid="back-btn" onClick={back}>← Back</OutlineButton>
              ) : <span />}
              {step < 3 ? (
                <PrimaryButton testid="next-btn" onClick={next} disabled={step === 1 && !step1Valid}>
                  Next →
                </PrimaryButton>
              ) : (
                <PrimaryButton testid="submit-btn" onClick={submit} disabled={!step3Valid || submitting}>
                  {submitting ? "Sending…" : (<><Send size={16} /> Send booking</>)}
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
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" } },
};

function FieldLabel({ children }) {
  return <div className="font-serif text-[20px] md:text-[22px] text-[var(--green-dark)] leading-snug">{children}</div>;
}

function SmallLabel({ children }) {
  return <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-muted)]">{children}</label>;
}

function ProgressBar({ step, total }) {
  return (
    <div className="mb-8" data-testid="step-dots">
      <div className="flex items-center gap-3 mb-3">
        {Array.from({ length: total }).map((_, i) => {
          const idx = i + 1;
          const active = idx <= step;
          return (
            <motion.div
              key={i}
              animate={{ width: idx === step ? 36 : 10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="h-1.5 rounded-full"
              style={{ background: active ? "var(--green)" : "var(--border-input)" }}
            />
          );
        })}
        <span className="ml-auto text-[11px] font-semibold tracking-[0.16em] uppercase text-[var(--text-muted)]">Step {step} of {total}</span>
      </div>
    </div>
  );
}
