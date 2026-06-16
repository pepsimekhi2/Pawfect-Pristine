import React from "react";
import { motion } from "framer-motion";
import { Sparkles, ShieldCheck, Star, Heart, Phone, Mail, MapPin } from "lucide-react";
import { PrimaryButton, GhostButton, PawSVG } from "./components/ui-kit";
import EtaCalculator from "./components/EtaCalculator";
import BookingForm from "./components/BookingForm";
import "./App.css";

const HERO_DOG = "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=900&q=80&auto=format&fit=crop";

const SERVICES = [
  { value: "general_cleaning", label: "General Cleaning", cat: "Home", emoji: "🧹", color: "var(--pp-pink)", span: "md:col-span-2", desc: "Kitchens, bathrooms, floors — spotless every visit." },
  { value: "deep_cleaning", label: "Deep Cleaning", cat: "Home", emoji: "✨", color: "var(--pp-yellow)", desc: "Behind appliances, inside cabinets, grout lines." },
  { value: "organizing", label: "Organizing", cat: "Home", emoji: "📦", color: "var(--pp-sage-light)", desc: "Sorted closets, systems that stick." },
  { value: "garage_shed", label: "Garages & Sheds", cat: "Home", emoji: "🏠", color: "var(--pp-terracotta-light)", desc: "Reclaim your space — even the chaotic ones." },
  { value: "dog_walking", label: "Dog Walking", cat: "Pet", emoji: "🐕", color: "var(--pp-sage-light)", span: "md:col-span-2", desc: "Daily walks, leash training, energy burn." },
  { value: "pet_sitting", label: "Pet Sitting", cat: "Pet", emoji: "🐱", color: "var(--pp-pink)", desc: "Overnight or drop-in — at home, comfy." },
  { value: "feeding_care", label: "Feeding & Care", cat: "Pet", emoji: "🍽️", color: "var(--pp-yellow)", desc: "Meals, meds, wellness check-ins." },
  { value: "playtime", label: "Playtime", cat: "Pet", emoji: "🎾", color: "var(--pp-terracotta-light)", desc: "Mental stimulation, fetch, bonding." },
];

const TESTIMONIALS = [
  { name: "Sarah L.", role: "Dog mom · weekly cleaning", text: "My house has never felt so clean — and my dog Biscuit absolutely loves the team. Treat every visit.", pet: "🐶" },
  { name: "Marcus R.", role: "Deep clean & garage", text: "They tackled my garage in one afternoon. I hadn't been able to park in it for two years. Life-changing.", pet: "🚗" },
  { name: "Jamie T.", role: "Pet sitting client", text: "Photo updates the whole trip. My two cats were calm and happy when I got back. Already rebooked.", pet: "🐱" },
  { name: "Priya K.", role: "Bi-weekly clean", text: "On time, every time. The squiggle in their schedule app is honestly adorable. 10/10.", pet: "✨" },
  { name: "Devon M.", role: "Dog walking 3×/wk", text: "My Aussie comes home actually tired. The team knows him by name. Could not ask for more.", pet: "🐕" },
];

const STATS = [
  { label: "Pet-safe products", value: "100%", icon: <Heart size={28} />, bg: "var(--pp-sage-light)" },
  { label: "Local rating", value: "5★", icon: <Star size={28} />, bg: "var(--pp-yellow)" },
  { label: "Same caregiver", value: "Always", icon: <Sparkles size={28} />, bg: "var(--pp-pink)" },
  { label: "Fully insured", value: "Yes", icon: <ShieldCheck size={28} />, bg: "var(--pp-terracotta-light)" },
];

const stagger = { animate: { transition: { staggerChildren: 0.07 } } };
const rise = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 220, damping: 22 } },
};

function Header() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md" style={{ background: "rgba(250, 247, 242, 0.85)", borderBottom: "2px solid var(--pp-ink)" }}>
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 md:px-12 py-4">
        <a href="#top" className="flex items-center gap-2.5 font-heading font-black text-xl md:text-2xl tracking-tight" data-testid="brand-logo">
          <PawSVG size={28} color="#E06D53" />
          Pawfect <span className="text-[var(--pp-terracotta)]">&</span> Pristine
        </a>
        <nav className="hidden md:flex items-center gap-7 font-bold text-[var(--pp-ink-soft)]">
          <a href="#services" className="hover:text-[var(--pp-terracotta)] transition-colors" data-testid="nav-services">Services</a>
          <a href="#eta" className="hover:text-[var(--pp-terracotta)] transition-colors" data-testid="nav-eta">ETA</a>
          <a href="#reviews" className="hover:text-[var(--pp-terracotta)] transition-colors" data-testid="nav-reviews">Reviews</a>
        </nav>
        <a href="#book" data-testid="header-book-cta">
          <GhostButton>Book a visit</GhostButton>
        </a>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section id="top" className="relative overflow-hidden px-6 md:px-12 lg:px-24 pt-12 md:pt-20 pb-16 md:pb-24">
      {/* Background squiggles */}
      <svg className="absolute -top-10 -left-10 opacity-50 pointer-events-none" width="280" height="200" viewBox="0 0 280 200" aria-hidden>
        <path d="M10 60 Q 50 10 90 60 T 170 60 T 250 60" stroke="#E06D53" strokeWidth="4" fill="none" strokeLinecap="round" />
        <path d="M30 120 Q 70 70 110 120 T 190 120 T 270 120" stroke="#89A894" strokeWidth="4" fill="none" strokeLinecap="round" />
      </svg>
      <div className="absolute top-10 right-10 float-paw" style={{ "--rot": "20deg" }}><PawSVG size={48} color="#89A894" /></div>
      <div className="absolute bottom-10 left-20 float-paw" style={{ "--rot": "-12deg", animationDelay: "1.2s" }}><PawSVG size={36} color="#E06D53" /></div>

      <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-10 lg:gap-14 items-center">
        <motion.div variants={stagger} initial="initial" animate="animate" className="lg:col-span-7">
          <motion.div variants={rise}>
            <span className="sticker"><MapPin size={14} /> Decatur · East Atlanta</span>
          </motion.div>
          <motion.h1 variants={rise} className="font-heading font-black tracking-tighter text-5xl sm:text-6xl md:text-7xl lg:text-[5.5rem] leading-[0.95] mt-5">
            Clean home.
            <br />
            <span className="italic font-normal" style={{ fontFamily: "'Bricolage Grotesque', serif" }}>
              <span className="squiggle-underline">Happy paws.</span>
            </span>
          </motion.h1>
          <motion.p variants={rise} className="text-[var(--pp-ink-soft)] mt-6 text-lg md:text-xl font-semibold max-w-xl leading-relaxed">
            Local home cleaning + heartfelt pet care, under one roof. We scrub. We snuggle. You relax.
          </motion.p>
          <motion.div variants={rise} className="flex flex-wrap gap-3 mt-8">
            <a href="#book" data-testid="hero-book-cta"><PrimaryButton>Book a visit 🐾</PrimaryButton></a>
            <a href="#services" data-testid="hero-services-cta"><GhostButton>See services</GhostButton></a>
          </motion.div>
          <motion.div variants={rise} className="flex flex-wrap items-center gap-2.5 mt-8">
            <span className="sticker" style={{ background: "var(--pp-sage-light)" }}>🏡 Locally owned</span>
            <span className="sticker" style={{ background: "var(--pp-pink)" }}>✓ Pet-safe products</span>
            <span className="sticker" style={{ background: "var(--pp-yellow)" }}>★★★★★ 5.0</span>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9, rotate: 4 }}
          animate={{ opacity: 1, scale: 1, rotate: -2 }}
          transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.1 }}
          className="lg:col-span-5 relative"
        >
          <div className="relative rounded-[36px] overflow-hidden border-2 border-ink shadow-pop-lg" style={{ transform: "rotate(2deg)" }}>
            <img src={HERO_DOG} alt="Happy dog on a clean couch" className="w-full h-[420px] md:h-[520px] object-cover" />
            <div className="absolute top-4 left-4">
              <span className="sticker" style={{ background: "var(--pp-pink)" }}>🐾 Biscuit, regular client</span>
            </div>
          </div>
          {/* Floating sticker */}
          <motion.div
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -bottom-6 -left-4 md:-left-10 bg-white border-2 border-ink rounded-2xl px-5 py-3 shadow-pop-lg rotate-[-6deg]"
          >
            <div className="font-heading font-black text-2xl leading-none">~18 min</div>
            <div className="text-xs uppercase font-extrabold tracking-wider text-[var(--pp-muted)]">avg arrival</div>
          </motion.div>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="absolute -top-5 -right-3 md:-right-8 bg-[var(--pp-sage)] text-white border-2 border-ink rounded-full px-4 py-2 shadow-pop rotate-[8deg]"
          >
            <div className="font-heading font-black text-sm">Wags + sparkles ✨</div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function Services() {
  return (
    <section id="services" className="px-6 md:px-12 lg:px-24 py-16 md:py-24">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
          <div>
            <span className="sticker"><Sparkles size={14} /> What we do</span>
            <h2 className="font-heading text-4xl md:text-6xl font-black mt-4 leading-[1.02] tracking-tight">
              Two things we love — <span className="squiggle-underline">done right.</span>
            </h2>
          </div>
          <p className="text-[var(--pp-ink-soft)] font-semibold max-w-md text-lg">
            Expert home cleaning & heartfelt pet care, scheduled around your week.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
          {SERVICES.map((s, i) => (
            <motion.a
              href="#book"
              key={s.value}
              data-testid={`service-card-${s.value}`}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: i * 0.05, type: "spring", stiffness: 200, damping: 20 }}
              whileHover={{ scale: 1.02, rotate: i % 2 === 0 ? -1 : 1, y: -6 }}
              className={`group rounded-3xl border-2 border-ink shadow-pop p-6 md:p-7 cursor-pointer ${s.span || ""}`}
              style={{ background: s.color }}
            >
              <div className="flex items-start justify-between">
                <div className="text-5xl md:text-6xl wiggle-on-hover">{s.emoji}</div>
                <span className="text-xs font-extrabold uppercase tracking-widest text-[var(--pp-ink-soft)]">{s.cat}</span>
              </div>
              <h3 className="font-heading font-black text-2xl md:text-3xl mt-4 leading-tight">{s.label}</h3>
              <p className="text-[var(--pp-ink-soft)] mt-2 font-semibold">{s.desc}</p>
              <div className="mt-5 inline-flex items-center gap-1 font-extrabold text-[var(--pp-ink)] group-hover:gap-3 transition-all">
                Book it <span>→</span>
              </div>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}

function Stats() {
  return (
    <section className="px-6 md:px-12 lg:px-24 py-14">
      <div className="max-w-7xl mx-auto grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            whileHover={{ y: -4, rotate: i % 2 === 0 ? -1 : 1 }}
            className="rounded-3xl border-2 border-ink p-6 shadow-pop"
            style={{ background: s.bg }}
          >
            <div className="text-[var(--pp-ink)]">{s.icon}</div>
            <div className="font-heading font-black text-3xl md:text-4xl mt-2 leading-none">{s.value}</div>
            <div className="text-xs md:text-sm font-extrabold uppercase tracking-wider text-[var(--pp-ink-soft)] mt-2">{s.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Testimonials() {
  const items = [...TESTIMONIALS, ...TESTIMONIALS];
  return (
    <section id="reviews" className="py-16 md:py-24 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
        <div className="text-center mb-10">
          <span className="sticker"><Heart size={14} /> Neighbors love us</span>
          <h2 className="font-heading text-4xl md:text-6xl font-black mt-4 leading-[1.02] tracking-tight">
            Real words from <span className="squiggle-underline">real clients.</span>
          </h2>
        </div>
      </div>
      <div className="relative" data-testid="testimonials-marquee">
        <div className="marquee-track">
          {items.map((t, i) => (
            <div key={i} className="w-[340px] md:w-[400px] shrink-0 rounded-3xl border-2 border-ink bg-white shadow-pop p-6 md:p-7" style={{ transform: i % 2 === 0 ? "rotate(-1deg)" : "rotate(1deg)" }}>
              <div className="text-2xl">★★★★★</div>
              <p className="mt-3 font-bold text-[var(--pp-ink-soft)] leading-relaxed">&ldquo;{t.text}&rdquo;</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="w-11 h-11 rounded-full border-2 border-ink flex items-center justify-center text-2xl" style={{ background: "var(--pp-pink)" }}>{t.pet}</div>
                <div>
                  <div className="font-heading font-black">{t.name}</div>
                  <div className="text-xs uppercase font-extrabold tracking-wider text-[var(--pp-muted)]">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="px-6 md:px-12 lg:px-24 py-12">
      <div className="max-w-5xl mx-auto rounded-[36px] border-2 border-ink p-10 md:p-16 text-center shadow-pop-lg relative overflow-hidden" style={{ background: "var(--pp-terracotta)" }}>
        <div className="absolute top-6 left-6 float-paw" style={{ "--rot": "-20deg" }}><PawSVG size={36} color="#FAF7F2" /></div>
        <div className="absolute bottom-6 right-6 float-paw" style={{ "--rot": "18deg", animationDelay: ".8s" }}><PawSVG size={42} color="#FAF7F2" /></div>
        <h3 className="font-heading text-4xl md:text-6xl font-black text-white leading-[1.02] tracking-tight">
          Ready for a cleaner home<br />& a happier pet?
        </h3>
        <p className="text-white/90 mt-4 font-semibold text-lg max-w-xl mx-auto">
          Book your first visit today. No contracts. Just sparkle and snuggles.
        </p>
        <div className="mt-7 flex flex-wrap gap-3 justify-center">
          <a href="#book" data-testid="cta-book"><GhostButton>Book a visit →</GhostButton></a>
          <a href="tel:+14703814682" data-testid="cta-call"><GhostButton><Phone size={16} /> (470) 381-4682</GhostButton></a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="mt-10 border-t-2 border-ink" style={{ background: "var(--pp-cream)" }}>
      <div className="hand-divider" />
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-10 md:py-14 grid md:grid-cols-3 gap-8">
        <div>
          <div className="flex items-center gap-2 font-heading font-black text-2xl">
            <PawSVG size={28} color="#E06D53" /> Pawfect & Pristine
          </div>
          <p className="mt-3 font-semibold text-[var(--pp-ink-soft)]">Clean homes. Happy paws. Local love.</p>
        </div>
        <div>
          <div className="font-extrabold uppercase tracking-wider text-sm text-[var(--pp-muted)]">Contact</div>
          <a href="tel:+14703814682" className="flex items-center gap-2 mt-2 font-bold hover:text-[var(--pp-terracotta)]"><Phone size={16} /> (470) 381-4682</a>
          <a href="mailto:hello@pawfectpristine.local" className="flex items-center gap-2 mt-2 font-bold hover:text-[var(--pp-terracotta)]"><Mail size={16} /> hello@pawfectpristine.local</a>
          <div className="flex items-center gap-2 mt-2 font-bold"><MapPin size={16} /> Decatur · East Atlanta</div>
        </div>
        <div>
          <div className="font-extrabold uppercase tracking-wider text-sm text-[var(--pp-muted)]">Service area</div>
          <p className="mt-2 font-semibold text-[var(--pp-ink-soft)]">0–7 mi: standard<br />7–13 mi: +$20 travel<br />13+ mi: call for a quote</p>
        </div>
      </div>
      <div className="text-center text-xs uppercase tracking-widest font-extrabold text-[var(--pp-muted)] py-5 border-t border-ink/20">
        © {new Date().getFullYear()} Pawfect & Pristine · Made with 🐾 in Decatur
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="App font-body">
      <Header />
      <main>
        <Hero />
        <Services />
        <Stats />
        <EtaCalculator />
        <Testimonials />
        <BookingForm />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
