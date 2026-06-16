import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, CheckCircle2, Send, ArrowLeft, CreditCard, Banknote, Wallet } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { SegmentedControl, PillToggle, Stepper, PrimaryButton, OutlineButton } from "../components/ui-kit";
import { CalendarPicker, TimePicker, FormattedDate, toIso } from "../components/CalendarPicker";

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

const TOTAL_STEPS = 5;

export default function BookPage() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [catalog, setCatalog] = useState(null);
  const [category, setCategory] = useState("home");
  const [serviceValue, setServiceValue] = useState("general_cleaning");
  const [tierKey, setTierKey] = useState(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [pets, setPets] = useState(0);
  const [notes, setNotes] = useState("");
  const [paymentPlan, setPaymentPlan] = useState("pay_later");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [tosAccepted, setTosAccepted] = useState(false);
  const [quote, setQuote] = useState(null);
  const [eta, setEta] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState("");
  // mock card
  const [cardNum, setCardNum] = useState("4242 4242 4242 4242");
  const [cardExp, setCardExp] = useState("12/29");
  const [cardCvc, setCardCvc] = useState("123");

  // Prefill from user
  useEffect(() => {
    if (user) {
      setName((n) => n || user.name);
      setPhone((p) => p || user.phone || "");
    }
  }, [user]);

  // Catalog
  useEffect(() => {
    api.get("/api/catalog").then((r) => {
      setCatalog(r.data);
      const svc = r.data[serviceValue];
      if (svc?.has_tiers && svc.tiers?.length) setTierKey(svc.tiers[0].key);
    });
  }, []); // eslint-disable-line

  const services = useMemo(() => {
    if (!catalog) return [];
    return Object.entries(catalog)
      .filter(([, s]) => s.category === category)
      .map(([k, s]) => ({ value: k, label: s.label, icon: s.icon }));
  }, [catalog, category]);

  const currentSvc = catalog?.[serviceValue];
  const currentTier = currentSvc?.tiers?.find((t) => t.key === tierKey);

  // Recompute quote on changes
  useEffect(() => {
    if (!serviceValue) return;
    const dateIso = date ? `${date}T${(time || "14:00")}:00Z` : null;
    api.post("/api/quote", { service_value: serviceValue, tier_key: tierKey, preferred_date: dateIso })
      .then((r) => setQuote(r.data))
      .catch(() => setQuote(null));
  }, [serviceValue, tierKey, date, time]);

  const onCategory = (cat) => {
    setCategory(cat);
    const list = Object.entries(catalog || {}).filter(([, s]) => s.category === cat);
    if (list.length) {
      const [k, s] = list[0];
      setServiceValue(k);
      setTierKey(s.tiers?.[0]?.key || null);
    }
  };

  const onPickService = (v) => {
    setServiceValue(v);
    const s = catalog?.[v];
    if (s?.has_tiers && s.tiers?.length) setTierKey(s.tiers[0].key);
  };

  const grandTotal = useMemo(() => {
    const base = quote?.total || 0;
    const travel = eta?.extra_fee || 0;
    return Math.round((base + travel) * 100) / 100;
  }, [quote, eta]);

  const dueNow = useMemo(() => {
    if (paymentPlan === "all_now") return grandTotal;
    if (paymentPlan === "half_now") return Math.round((grandTotal / 2) * 100) / 100;
    return 0;
  }, [paymentPlan, grandTotal]);

  // ETA on address change (debounced)
  useEffect(() => {
    if (!address || address.length < 6) { setEta(null); return; }
    const t = setTimeout(async () => {
      try {
        const { data } = await api.post("/api/eta", { address });
        setEta(data);
      } catch { setEta(null); }
    }, 700);
    return () => clearTimeout(t);
  }, [address]);

  const next = () => setStep((s) => Math.min(TOTAL_STEPS, s + 1));
  const back = () => setStep((s) => Math.max(1, s - 1));

  const s1Valid = serviceValue && (!currentSvc?.has_tiers || tierKey);
  const s2Valid = !!date && !!time;
  const s3Valid = name.trim() && phone.trim() && address.trim();
  const s4Valid = (paymentPlan === "pay_later" || paymentMethod === "cash")
    ? true
    : (cardNum.replace(/\s/g,"").length >= 12 && cardExp.length >= 4 && cardCvc.length >= 3);
  const s5Valid = tosAccepted;

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const { data } = await api.post("/api/bookings", {
        name, phone, address,
        service_value: serviceValue,
        tier_key: tierKey,
        pets,
        notes,
        preferred_date: date,
        preferred_time: time,
        payment_plan: paymentPlan,
        payment_method: paymentMethod,
        tos_accepted: true,
      });
      setSuccess(data);
      fireConfetti();
      setStep(TOTAL_STEPS + 1);
    } catch (err) {
      setError(err?.response?.data?.detail || "Couldn't submit. Try again.");
    } finally { setSubmitting(false); }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-soft)]">
      <header className="bg-white border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <Link to={user ? "/dashboard" : "/"} className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[var(--green)] uppercase tracking-[0.16em] hover:opacity-70" data-testid="book-back">
            <ArrowLeft size={14} /> {user ? "Back to dashboard" : "Back to home"}
          </Link>
          {!user && (
            <Link to="/login" state={{ from: "/book" }} className="text-[12px] uppercase tracking-[0.16em] font-semibold text-[var(--green)] hover:opacity-70" data-testid="book-signin">Sign in</Link>
          )}
        </div>
      </header>
      <div className="max-w-3xl mx-auto px-6 md:px-10 py-10 md:py-14">
        <div className="text-center mb-10">
          <span className="eyebrow"><Sparkles size={12} className="inline mr-1 -mt-0.5" />Book a visit</span>
          <h1 className="font-serif text-3xl md:text-5xl font-bold mt-3 text-[var(--green-dark)] leading-tight tracking-tight">
            Let&rsquo;s get you <span className="italic-green">booked.</span>
          </h1>
          <p className="text-[var(--text-muted)] mt-3 text-[15px] leading-relaxed max-w-md mx-auto">
            A few quick steps. No contracts. We&rsquo;ll text you back fast.
          </p>
        </div>

        <div className="bg-white border border-[var(--border)] rounded-[20px] shadow-sm p-6 md:p-10">
          {step <= TOTAL_STEPS && <ProgressBar step={step} total={TOTAL_STEPS} />}

          <AnimatePresence initial={false} mode="wait">
            {step === 1 && (
              <motion.div key="s1" {...fade} className="space-y-6">
                <FieldLabel>Are we cleaning a home or caring for a pet?</FieldLabel>
                <SegmentedControl
                  testid="cat-segmented"
                  value={category}
                  onChange={onCategory}
                  options={[
                    { value: "home", label: "Home", icon: "🏡" },
                    { value: "pet", label: "Pet", icon: "🐾" },
                  ]}
                />
                <FieldLabel>Pick a service</FieldLabel>
                <PillToggle testid="service-pills" options={services} value={serviceValue} onChange={onPickService} />
                {currentSvc?.has_tiers && (
                  <>
                    <FieldLabel>{currentSvc.tier_question}</FieldLabel>
                    <div className="grid sm:grid-cols-2 gap-3" data-testid="tier-cards">
                      {currentSvc.tiers.map((t) => {
                        const sel = tierKey === t.key;
                        return (
                          <button
                            type="button"
                            key={t.key}
                            data-testid={`tier-${t.key}`}
                            onClick={() => setTierKey(t.key)}
                            className={`tier-card ${sel ? "is-selected" : ""}`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="font-semibold text-[15px] text-[var(--text)]">{t.label}</div>
                                <div className="text-[12px] text-[var(--text-muted)] mt-1">{t.desc}</div>
                              </div>
                              <div className="font-serif text-[22px] text-[var(--green-dark)] leading-none">${t.price}</div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="s2" {...fade} className="space-y-6">
                <FieldLabel>When works for you?</FieldLabel>
                <CalendarPicker value={date} onChange={setDate} testid="book-calendar" />
                {date && (
                  <div className="text-[13px] text-[var(--text-muted)] flex items-center justify-between">
                    <div><FormattedDate iso={date} /></div>
                    {quote?.is_advance && (
                      <span className="tag tag-pet" data-testid="advance-tag">+$0.99 advance fee</span>
                    )}
                  </div>
                )}
                <FieldLabel>Pick a time</FieldLabel>
                <TimePicker value={time} onChange={setTime} testid="book-time" />
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
                  {eta && (
                    <div className="text-[12px] text-[var(--text-muted)] mt-2" data-testid="eta-inline">
                      ~{eta.distance_miles} mi · {Math.round(eta.duration_minutes)} min{eta.extra_fee > 0 ? ` · +$${eta.extra_fee} travel fee` : " · standard zone"}
                    </div>
                  )}
                </div>
                {category === "pet" ? (
                  <Stepper testid="pet-stepper" label="Number of pets" value={Math.max(1, pets)} onChange={setPets} min={1} max={10} />
                ) : (
                  <Stepper testid="home-pets-stepper" label="Pets in the home" value={pets} onChange={setPets} min={0} max={10} />
                )}
                <div>
                  <SmallLabel>Anything we should know?</SmallLabel>
                  <textarea data-testid="notes-input" className="pp-input mt-1.5" placeholder="Skittish cat, allergies, gate code, etc." value={notes} onChange={(e) => setNotes(e.target.value)} />
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="s4" {...fade} className="space-y-5">
                <FieldLabel>How would you like to pay?</FieldLabel>
                <div className="grid gap-3" data-testid="payment-plans">
                  <PlanCard
                    selected={paymentPlan === "pay_later"}
                    onClick={() => setPaymentPlan("pay_later")}
                    testid="plan-pay_later"
                    title="Pay on arrival"
                    desc="No charge today. Pay when we arrive — cash or card."
                    amount={`$0 now · $${grandTotal} on arrival`}
                    icon="⏰"
                  />
                  <PlanCard
                    selected={paymentPlan === "half_now"}
                    onClick={() => setPaymentPlan("half_now")}
                    testid="plan-half_now"
                    title="Pay half now"
                    desc="Reserve your spot with half. The rest is due on arrival."
                    amount={`$${Math.round((grandTotal/2)*100)/100} now · $${Math.round((grandTotal/2)*100)/100} on arrival`}
                    icon="⚖️"
                  />
                  <PlanCard
                    selected={paymentPlan === "all_now"}
                    onClick={() => setPaymentPlan("all_now")}
                    testid="plan-all_now"
                    title="Pay in full now"
                    desc="Get it out of the way. We&rsquo;ll just show up and do the work."
                    amount={`$${grandTotal} now · $0 on arrival`}
                    icon="✨"
                  />
                </div>

                <div className="h-px bg-[var(--border)] my-2" />

                <FieldLabel>Payment method</FieldLabel>
                <div className="grid sm:grid-cols-2 gap-3" data-testid="payment-methods">
                  <MethodCard
                    selected={paymentMethod === "card"}
                    onClick={() => setPaymentMethod("card")}
                    testid="method-card"
                    icon={<CreditCard size={18} />}
                    title="Tap to pay / card"
                    desc="Apple Pay, Google Pay, or card."
                  />
                  <MethodCard
                    selected={paymentMethod === "cash"}
                    onClick={() => setPaymentMethod("cash")}
                    testid="method-cash"
                    icon={<Banknote size={18} />}
                    title="Cash on arrival"
                    desc="Pay our team in person."
                    disabled={paymentPlan !== "pay_later"}
                    disabledReason="Cash is only available with 'Pay on arrival'."
                  />
                </div>

                {paymentPlan !== "pay_later" && paymentMethod === "card" && (
                  <div className="card-form bg-[var(--green-light)]/60 border border-[var(--border)] rounded-[16px] p-5 mt-2" data-testid="mock-card-form">
                    <div className="flex items-center gap-2 text-[12px] uppercase tracking-[0.14em] font-semibold text-[var(--green)] mb-3">
                      <Wallet size={14} /> Pay now — secure card details (mocked for demo)
                    </div>
                    <div className="grid gap-3">
                      <div>
                        <SmallLabel>Card number</SmallLabel>
                        <input className="pp-input mt-1.5 tabular-nums" data-testid="card-number" value={cardNum} onChange={(e) => setCardNum(e.target.value)} />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <SmallLabel>Expiry (MM/YY)</SmallLabel>
                          <input className="pp-input mt-1.5" data-testid="card-exp" value={cardExp} onChange={(e) => setCardExp(e.target.value)} />
                        </div>
                        <div>
                          <SmallLabel>CVC</SmallLabel>
                          <input className="pp-input mt-1.5" data-testid="card-cvc" value={cardCvc} onChange={(e) => setCardCvc(e.target.value)} />
                        </div>
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-1">
                        Stripe integration coming soon. No real card is charged.
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {step === 5 && (
              <motion.div key="s5" {...fade} className="space-y-5">
                <FieldLabel>Review &amp; confirm</FieldLabel>
                <div className="review-card" data-testid="review-card">
                  <Row k="Service" v={<>{currentSvc?.label}{currentTier ? <span className="text-[var(--text-muted)]"> · {currentTier.label}</span> : null}</>} />
                  <Row k="When" v={<><FormattedDate iso={date} /> {time && <span className="text-[var(--text-muted)]">at {time}</span>}</>} />
                  <Row k="Where" v={address} />
                  <Row k="Contact" v={`${name} · ${phone}`} />
                  <div className="h-px bg-[var(--border)] my-3" />
                  <Row k="Service price" v={`$${quote?.base_price ?? 0}`} />
                  {quote?.is_advance && <Row k="Advance fee (≥7 days out)" v={`$${quote.advance_fee}`} />}
                  {eta?.extra_fee > 0 && <Row k="Travel fee" v={`$${eta.extra_fee}`} />}
                  <Row k="Total" v={<span className="font-serif text-[22px] text-[var(--green-dark)]">${grandTotal}</span>} strong />
                  <div className="h-px bg-[var(--border)] my-3" />
                  <Row k="Due now" v={<span className="font-semibold text-[var(--green-dark)]">${dueNow}</span>} />
                  <Row k="Due on arrival" v={`$${Math.round((grandTotal-dueNow)*100)/100}`} />
                  <Row k="Method" v={paymentMethod === "card" ? "Tap-to-pay / card" : "Cash on arrival"} />
                </div>
                <label className="tos-row" data-testid="tos-row">
                  <input type="checkbox" data-testid="tos-checkbox" checked={tosAccepted} onChange={(e) => setTosAccepted(e.target.checked)} />
                  <span>I agree to the <Link to="/tos" target="_blank" className="text-[var(--green)] font-semibold hover:underline" data-testid="tos-link">Terms of Service</Link> &amp; cancellation policy.</span>
                </label>
                {error && <div className="auth-error" data-testid="book-error">{error}</div>}
              </motion.div>
            )}

            {step === TOTAL_STEPS + 1 && success && (
              <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-6" data-testid="booking-success">
                <motion.div initial={{ scale: 0, rotate: -90 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }} className="inline-block">
                  <CheckCircle2 size={80} className="text-[var(--green)]" strokeWidth={1.5} />
                </motion.div>
                <h3 className="font-serif text-3xl md:text-4xl text-[var(--green-dark)] mt-5">You&rsquo;re <span className="italic-green">booked.</span></h3>
                <p className="text-[var(--text-muted)] mt-3 text-[15px] leading-relaxed max-w-md mx-auto">
                  Thanks, {name}. We just logged your visit. Total <strong>${success.grand_total}</strong>
                  {success.due_now > 0 ? <> (${success.due_now} captured today)</> : null}.
                </p>
                <div className="mt-7 flex flex-wrap gap-3 justify-center">
                  {user ? (
                    <Link to="/dashboard"><PrimaryButton testid="go-dashboard">Go to my dashboard</PrimaryButton></Link>
                  ) : (
                    <Link to="/signup"><PrimaryButton testid="go-signup">Create an account to track it</PrimaryButton></Link>
                  )}
                  <Link to="/"><OutlineButton testid="go-home">Back to home</OutlineButton></Link>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {step <= TOTAL_STEPS && (
            <div className="flex items-center justify-between mt-9 pt-6 border-t border-[var(--border)]">
              {step > 1 ? (<OutlineButton testid="back-btn" onClick={back}>← Back</OutlineButton>) : <span />}
              {step < TOTAL_STEPS ? (
                <PrimaryButton testid="next-btn" onClick={next}
                  disabled={
                    (step === 1 && !s1Valid) ||
                    (step === 2 && !s2Valid) ||
                    (step === 3 && !s3Valid) ||
                    (step === 4 && !s4Valid)
                  }>
                  Next →
                </PrimaryButton>
              ) : (
                <PrimaryButton testid="submit-btn" onClick={submit} disabled={!s5Valid || submitting}>
                  {submitting ? "Sending\u2026" : (<><Send size={16} /> Confirm booking</>)}
                </PrimaryButton>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const fade = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.28, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15, ease: "easeIn" } },
};

function FieldLabel({ children }) {
  return <div className="font-serif text-[20px] md:text-[22px] text-[var(--green-dark)] leading-snug">{children}</div>;
}
function SmallLabel({ children }) {
  return <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-muted)]">{children}</label>;
}
function Row({ k, v, strong }) {
  return (
    <div className={`flex items-center justify-between gap-3 py-1 text-[13px] ${strong ? "font-medium" : ""}`}>
      <span className="text-[var(--text-muted)]">{k}</span>
      <span className="text-[var(--text)] text-right">{v}</span>
    </div>
  );
}
function PlanCard({ selected, onClick, testid, title, desc, amount, icon }) {
  return (
    <button type="button" onClick={onClick} data-testid={testid} className={`plan-card ${selected ? "is-selected" : ""}`}>
      <div className="flex items-start gap-4">
        <div className="plan-icon">{icon}</div>
        <div className="flex-1 text-left">
          <div className="font-semibold text-[15px] text-[var(--text)]">{title}</div>
          <div className="text-[12px] text-[var(--text-muted)] mt-0.5">{desc}</div>
          <div className="text-[12px] text-[var(--green-dark)] font-medium mt-2">{amount}</div>
        </div>
      </div>
    </button>
  );
}
function MethodCard({ selected, onClick, testid, icon, title, desc, disabled, disabledReason }) {
  return (
    <button
      type="button"
      onClick={() => { if (!disabled) onClick(); }}
      data-testid={testid}
      disabled={disabled}
      title={disabled ? disabledReason : ""}
      className={`method-card ${selected ? "is-selected" : ""} ${disabled ? "is-disabled" : ""}`}
    >
      <div className="flex items-center gap-3">
        <span className="method-icon">{icon}</span>
        <div className="text-left">
          <div className="font-semibold text-[14px] text-[var(--text)]">{title}</div>
          <div className="text-[12px] text-[var(--text-muted)] mt-0.5">{desc}</div>
        </div>
      </div>
    </button>
  );
}
function ProgressBar({ step, total }) {
  return (
    <div className="mb-8" data-testid="step-dots">
      <div className="flex items-center gap-3 mb-3">
        {Array.from({ length: total }).map((_, i) => {
          const idx = i + 1;
          const active = idx <= step;
          return (
            <motion.div key={i} animate={{ width: idx === step ? 36 : 10 }} transition={{ duration: 0.3, ease: "easeOut" }} className="h-1.5 rounded-full" style={{ background: active ? "var(--green)" : "var(--border-input)" }} />
          );
        })}
        <span className="ml-auto text-[11px] font-semibold tracking-[0.16em] uppercase text-[var(--text-muted)]">Step {step} of {total}</span>
      </div>
    </div>
  );
}
