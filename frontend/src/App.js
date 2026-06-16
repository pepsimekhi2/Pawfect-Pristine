import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Phone, Mail, MapPin, Calendar, Check } from "lucide-react";
import { PrimaryButton, OutlineButton, GhostWhiteButton } from "./components/ui-kit";
import EtaCalculator from "./components/EtaCalculator";
import HeaderAuth from "./components/HeaderAuth";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import BookPage from "./pages/BookPage";
import TosPage from "./pages/TosPage";
import AdminPage from "./pages/AdminPage";
import RequireAdmin from "./components/RequireAdmin";
import RequireAuth from "./components/RequireAuth";
import "./App.css";

const IMG = {
  heroDog: "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=900&auto=format&fit=crop&q=80",
  cleanHome: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=900&auto=format&fit=crop&q=80",
  dogWalk: "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=600&auto=format&fit=crop&q=80",
  catDog: "https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=600&auto=format&fit=crop&q=80",
  puppy: "https://images.unsplash.com/photo-1601758124510-52d02ddb7cbd?w=600&auto=format&fit=crop&q=80",
};

const SERVICES = [
  { value: "general_cleaning", label: "General Cleaning", cat: "Home", emoji: "🧹", iconClass: "svc-icon-green", desc: "Full home refresh — kitchens, bathrooms, floors, and surfaces spotless every visit." },
  { value: "deep_cleaning", label: "Deep Cleaning", cat: "Home", emoji: "✨", iconClass: "svc-icon-green", desc: "Behind appliances, inside cabinets, grout lines — a thorough top-to-bottom reset." },
  { value: "organizing", label: "Organizing", cat: "Home", emoji: "📦", iconClass: "svc-icon-green", desc: "Clutter-free spaces, sorted closets, and systems that actually stick long-term." },
  { value: "garage_shed", label: "Garages & Sheds", cat: "Home", emoji: "🏠", iconClass: "svc-icon-green", desc: "Reclaim your garage. We sort, sweep, and organize even the most chaotic spaces." },
  { value: "dog_walking", label: "Dog Walking", cat: "Pet", emoji: "🐕", iconClass: "svc-icon-warm", desc: "Daily walks, leash training, and exercise for dogs of all sizes and energy levels." },
  { value: "pet_sitting", label: "Pet Sitting", cat: "Pet", emoji: "🐱", iconClass: "svc-icon-warm", desc: "In-home overnight or drop-in sitting — your pets stay comfortable in their own space." },
  { value: "feeding_care", label: "Feeding & Care", cat: "Pet", emoji: "🍽️", iconClass: "svc-icon-warm", desc: "Regular feedings, fresh water, medication reminders, and wellness check-ins." },
  { value: "playtime", label: "Playtime & Enrichment", cat: "Pet", emoji: "🎾", iconClass: "svc-icon-warm", desc: "Mental stimulation, toys, fetch, and bonding time to keep your pets happy and thriving." },
];

const BENEFITS = [
  "Eco-friendly, pet-safe products",
  "Flexible scheduling around your life",
  "Garages, sheds & outdoor spaces too",
  "Detailed checklists — nothing missed",
];

const TESTIMONIALS = [
  { name: "Sarah L.", role: "Dog mom & weekly cleaning client", text: "My house has never felt so clean — and my dog Biscuit absolutely loves the team. They bring him a treat every single visit. I can\u2019t recommend them enough!", initials: "SL" },
  { name: "Marcus R.", role: "Deep clean & garage organizing", text: "They tackled my garage in one afternoon — I hadn\u2019t been able to park in it for two years. Now it\u2019s spotless and organized. Genuinely life-changing.", initials: "MR" },
  { name: "Jamie T.", role: "Pet sitting client", text: "I was nervous to leave my two cats, but they sent photo updates the whole trip. My cats were calm and happy when I got back. Already rebooked for next month.", initials: "JT" },
];

const STATS = [
  { value: "100%", label: "Pet-safe cleaning products used in every home" },
  { value: "5★", label: "Consistently rated by happy local pet owners" },
  { value: "Same", label: "Caregiver every visit — your pet knows us by name" },
  { value: "Insured", label: "Fully covered so you can leave worry-free" },
];

const rise = {
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
};

function Logo({ onDark = false }) {
  return (
    <Link to="/" className="flex items-center gap-2.5" data-testid="brand-logo">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: onDark ? "var(--green-pale)" : "var(--green)", color: onDark ? "var(--green-dark)" : "#fff" }}>
        <span className="text-lg leading-none">🐾</span>
      </div>
      <div className="flex flex-col leading-tight">
        <span className="font-serif text-[18px] font-bold" style={{ color: onDark ? "#c8e8d8" : "var(--green-dark)" }}>Pawfect &amp; Pristine</span>
        <span className="text-[9px] uppercase tracking-[0.18em] font-medium" style={{ color: onDark ? "var(--green-pale)" : "var(--green-muted)" }}>Home & Pet Services</span>
      </div>
    </Link>
  );
}

function Nav() {
  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-[#f0ede8] px-6 md:px-12 h-16 flex items-center justify-between">
      <Logo />
      <div className="hidden md:flex items-center gap-7 text-[13px] font-medium">
        <a href="#services" className="link-underline" data-testid="nav-services">Services</a>
        <a href="#about" className="link-underline" data-testid="nav-about">About</a>
        <a href="#eta" className="link-underline" data-testid="nav-eta">ETA</a>
        <a href="#reviews" className="link-underline" data-testid="nav-reviews">Reviews</a>
      </div>
      <HeaderAuth />
    </nav>
  );
}

function Hero() {
  return (
    <section id="top" className="relative">
      <div className="grid lg:grid-cols-2 min-h-[560px]">
        {/* Left */}
        <div className="hero-gradient px-6 md:px-12 lg:px-16 py-16 md:py-24 flex flex-col justify-center">
          <motion.span {...rise} className="eyebrow">Local Home &amp; Pet Services · Decatur &amp; East Atlanta</motion.span>
          <motion.h1
            {...rise}
            transition={{ ...rise.transition, delay: 0.05 }}
            className="font-serif text-[42px] md:text-[58px] lg:text-[64px] font-bold leading-[1.05] tracking-tight mt-5 text-[var(--green-dark)]"
          >
            Clean home,<br />
            <span className="italic-green">Happy Paws.</span>
          </motion.h1>
          <motion.p {...rise} transition={{ ...rise.transition, delay: 0.1 }} className="mt-5 max-w-md text-[15px] leading-[1.7] text-[#4a6a57]">
            A clean home and a happy pet makes a better day — every single day. We handle the scrubbing and the snuggling so you don&rsquo;t have to.
          </motion.p>
          <motion.div {...rise} transition={{ ...rise.transition, delay: 0.15 }} className="flex flex-wrap gap-3 mt-8">
            <Link to="/book" data-testid="hero-book-cta"><PrimaryButton testid="hero-book-btn">Book a Visit</PrimaryButton></Link>
            <a href="#services" data-testid="hero-services-cta"><OutlineButton testid="hero-services-btn">Our Services</OutlineButton></a>
          </motion.div>
        </div>

        {/* Right */}
        <div className="relative bg-[var(--green-light)] overflow-hidden">
          <motion.img
            initial={{ scale: 1.05, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
            src={IMG.heroDog}
            alt="Happy dog on a clean couch"
            className="absolute inset-0 w-full h-full object-cover"
          />
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="absolute bottom-6 left-6 hero-badge"
          >
            <span className="dot" /> Locally owned &amp; operated 🏡
          </motion.div>
        </div>
      </div>

      {/* Service strip */}
      <div className="border-y border-[var(--border)] bg-white">
        <div className="max-w-6xl mx-auto px-6 md:px-12 py-5 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-[12px] font-medium text-[var(--text-muted)]">
          {["🧹 Home Cleaning", "🐕 Dog Walking", "🐱 Pet Sitting", "📦 Organizing", "🏠 Garages & Sheds", "🐾 Play & Care"].map((s, i) => (
            <React.Fragment key={s}>
              {i > 0 && <span className="w-1 h-1 rounded-full bg-[var(--green-pale)]" />}
              <span>{s}</span>
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}

function Services() {
  return (
    <section id="services" className="px-6 md:px-12 py-20 md:py-28">
      <div className="max-w-6xl mx-auto">
        <motion.div {...rise} className="text-center mb-12">
          <span className="eyebrow">What We Do</span>
          <h2 className="font-serif text-3xl md:text-[44px] font-bold mt-3 text-[var(--green-dark)] leading-tight">
            Two things we love — <span className="italic-green">done right</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-3 text-[15px] max-w-xl mx-auto leading-relaxed">
            Expert home cleaning &amp; heartfelt pet care, under one roof.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {SERVICES.map((s, i) => (
            <motion.div
              key={s.value}
              data-testid={`service-card-${s.value}`}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ delay: i * 0.04, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            >
              <Link to="/book" className="card-clean group block">
                <div className={`svc-icon ${s.iconClass} transition-transform group-hover:scale-110`}>{s.emoji}</div>
                <h3 className="mt-4 font-semibold text-[15px] text-[var(--text)]">{s.label}</h3>
                <p className="mt-2 text-[13px] leading-[1.6] text-[var(--text-muted)]">{s.desc}</p>
                <span className={`tag ${s.cat === "Home" ? "tag-home" : "tag-pet"} mt-4`}>{s.cat}</span>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SplitHome() {
  return (
    <section id="about" className="px-6 md:px-12 py-20 md:py-24 bg-[var(--bg-soft)]">
      <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
        <motion.div {...rise} className="rounded-2xl overflow-hidden">
          <img src={IMG.cleanHome} alt="Clean bright living room" className="w-full h-[360px] md:h-[460px] object-cover" />
        </motion.div>
        <motion.div {...rise} transition={{ ...rise.transition, delay: 0.1 }}>
          <span className="eyebrow">Home Cleaning</span>
          <h2 className="font-serif text-3xl md:text-[40px] font-bold mt-3 text-[var(--green-dark)] leading-tight">
            Your home, <span className="italic-green">always at its best.</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-4 text-[15px] leading-[1.7] max-w-md">
            From regular maintenance cleans to one-time deep cleans before guests arrive — we show up reliably and leave everything shining.
          </p>
          <ul className="mt-6 space-y-3">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-start gap-3 text-[14px] text-[var(--text-soft)]">
                <span className="mt-0.5 w-5 h-5 rounded-full flex items-center justify-center" style={{ background: "var(--green-light)", color: "var(--green)" }}>
                  <Check size={12} strokeWidth={3} />
                </span>
                {b}
              </li>
            ))}
          </ul>
          <div className="mt-7">
            <Link to="/book"><PrimaryButton testid="split-book-btn">Book a Cleaning Visit</PrimaryButton></Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function PetsBlock() {
  return (
    <section className="px-6 md:px-12 py-20 md:py-24">
      <div className="max-w-6xl mx-auto">
        <motion.div {...rise} className="text-center mb-10">
          <span className="eyebrow">Pet Services</span>
          <h2 className="font-serif text-3xl md:text-[40px] font-bold mt-3 text-[var(--green-dark)] leading-tight">
            Your pets are family. <span className="italic-green">We treat them that way.</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-3 text-[15px] max-w-xl mx-auto leading-relaxed">
            Every visit is filled with patience, love, and lots of tail wags.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-3 gap-5">
          {[
            { src: IMG.dogWalk, label: "🐕 Dog Walking" },
            { src: IMG.catDog, label: "🐾 Pet Sitting" },
            { src: IMG.puppy, label: "🎾 Playtime" },
          ].map((p, i) => (
            <motion.div
              key={p.label}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: i * 0.06, duration: 0.5 }}
              className="relative rounded-2xl overflow-hidden aspect-square group"
            >
              <img src={p.src} alt={p.label} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
              <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/55 via-black/15 to-transparent">
                <span className="text-white font-medium text-[14px]">{p.label}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Stats() {
  return (
    <section className="px-6 md:px-12 py-16 bg-[var(--green-light)]">
      <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06, duration: 0.5 }}
            className="text-center"
          >
            <div className="font-serif text-[36px] md:text-[44px] font-bold text-[var(--green-dark)] leading-none">{s.value}</div>
            <div className="text-[12px] text-[var(--text-muted)] mt-2 leading-snug max-w-[200px] mx-auto">{s.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Testimonials() {
  return (
    <section id="reviews" className="px-6 md:px-12 py-20 md:py-28">
      <div className="max-w-6xl mx-auto">
        <motion.div {...rise} className="text-center mb-12">
          <span className="eyebrow">Happy Clients</span>
          <h2 className="font-serif text-3xl md:text-[44px] font-bold mt-3 text-[var(--green-dark)] leading-tight">
            Neighbors love us. <span className="italic-green">So do their pets.</span>
          </h2>
          <p className="text-[var(--text-muted)] mt-3 text-[15px] max-w-xl mx-auto leading-relaxed">
            Real words from real clients in our community.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-5" data-testid="testimonials-grid">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: i * 0.08, duration: 0.55 }}
              className="testi-card"
            >
              <div className="stars">★★★★★</div>
              <p className="mt-3 text-[13px] italic leading-[1.7] text-[var(--text-soft)]">&ldquo;{t.text}&rdquo;</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="testi-avatar">{t.initials}</div>
                <div>
                  <div className="text-[14px] font-semibold text-[var(--text)]">{t.name}</div>
                  <div className="text-[11px] text-[var(--text-muted)] mt-0.5">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="px-6 md:px-12 py-16">
      <div className="max-w-5xl mx-auto cta-gradient rounded-[28px] p-10 md:p-16 text-center text-white">
        <span className="text-[11px] uppercase tracking-[0.18em] font-semibold text-[var(--green-pale)]">Let&rsquo;s Get Started</span>
        <h3 className="font-serif text-3xl md:text-[44px] font-bold mt-3 leading-[1.1]">
          Ready for a cleaner home<br />&amp; a happier pet?
        </h3>
        <p className="text-white/85 mt-4 max-w-xl mx-auto text-[15px] leading-relaxed">
          Book your first visit today — no contracts, no stress. Just a cleaner home and a pet who can&rsquo;t wait for us to come back.
        </p>
        <div className="mt-7 flex flex-wrap gap-3 justify-center">
          <Link to="/book" data-testid="cta-book">
            <motion.button whileHover={{ y: -1 }} whileTap={{ scale: 0.97 }} className="btn-white">
              Book a Visit
            </motion.button>
          </Link>
          <a href="#services" data-testid="cta-services"><GhostWhiteButton>View Services</GhostWhiteButton></a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const cols = [
    { title: "Home Services", links: ["General Cleaning", "Deep Cleaning", "Organizing", "Garages & Sheds"] },
    { title: "Pet Care", links: ["Dog Walking", "Pet Sitting", "Feeding & Care", "Playtime"] },
  ];
  return (
    <footer style={{ background: "var(--green-deep-bg)" }} className="text-[#c8e8d8] mt-10">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-14 grid md:grid-cols-4 gap-10">
        <div>
          <Logo onDark />
          <p className="mt-4 text-[13px] leading-[1.7] text-[#7a9e8a] max-w-xs">
            A clean home &amp; happy pet makes a better day. Locally owned, serving Decatur &amp; East Atlanta.
          </p>
        </div>
        {cols.map((col) => (
          <div key={col.title}>
            <h4 className="text-[12px] font-semibold uppercase tracking-[0.12em] text-[#7aaa90]">{col.title}</h4>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l}><a href="#services" className="text-[13px] text-[#6b8878] hover:text-[var(--green-pale)] transition-colors">{l}</a></li>
              ))}
            </ul>
          </div>
        ))}
        <div>
          <h4 className="text-[12px] font-semibold uppercase tracking-[0.12em] text-[#7aaa90]">Contact</h4>
          <ul className="mt-4 space-y-2.5 text-[13px] text-[#6b8878]">
            <li><a href="tel:+14703814682" className="flex items-center gap-2 hover:text-[var(--green-pale)] transition-colors"><Phone size={14} /> (470) 381-4682</a></li>
            <li><a href="mailto:hello@pawfectpristine.com" className="flex items-center gap-2 hover:text-[var(--green-pale)] transition-colors"><Mail size={14} /> hello@pawfectpristine.com</a></li>
            <li className="flex items-center gap-2"><MapPin size={14} /> Decatur · East Atlanta</li>
            <li><Link to="/book" className="flex items-center gap-2 hover:text-[var(--green-pale)] transition-colors"><Calendar size={14} /> Book a Visit</Link></li>
            <li><Link to="/tos" className="flex items-center gap-2 hover:text-[var(--green-pale)] transition-colors" data-testid="footer-tos">Terms of Service</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-[#1a2f24]">
        <div className="max-w-6xl mx-auto px-6 md:px-12 py-5 flex flex-wrap items-center justify-between gap-3 text-[11px] text-[#5d7a6b]">
          <div>© {new Date().getFullYear()} Pawfect &amp; Pristine. All rights reserved.</div>
          <div>Made with 🐾 for pets &amp; their people.</div>
        </div>
      </div>
    </footer>
  );
}

function HomePage() {
  return (
    <div className="App font-sans">
      <Nav />
      <main>
        <Hero />
        <Services />
        <SplitHome />
        <PetsBlock />
        <Stats />
        <EtaCalculator />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/book" element={<BookPage />} />
      <Route path="/tos" element={<TosPage />} />
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
      <Route path="/admin" element={<RequireAdmin><AdminPage /></RequireAdmin>} />
      <Route path="*" element={<HomePage />} />
    </Routes>
  );
}
