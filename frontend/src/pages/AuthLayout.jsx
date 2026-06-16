import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";

const HERO_IMG = "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=900&auto=format&fit=crop&q=80";

export default function AuthLayout({ eyebrow, title, subtitle, children }) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-[var(--bg-soft)]">
      <div className="px-6 md:px-12 lg:px-16 py-10 md:py-14 flex flex-col justify-center">
        <div className="max-w-md w-full mx-auto">
          <Link to="/" className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[var(--green)] uppercase tracking-[0.16em] mb-8 hover:opacity-70" data-testid="auth-back-home">
            <ArrowLeft size={14} /> Back to home
          </Link>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
            <span className="eyebrow">{eyebrow}</span>
            <h1 className="font-serif text-[34px] md:text-[44px] font-bold mt-3 text-[var(--green-dark)] leading-tight">
              {title}
            </h1>
            <p className="text-[var(--text-muted)] mt-3 text-[15px] leading-[1.7]">{subtitle}</p>
            <div className="mt-8">{children}</div>
          </motion.div>
        </div>
      </div>
      <div className="relative hidden lg:block bg-[var(--green-light)]">
        <img src={HERO_IMG} alt="Happy dog" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-[rgba(15,32,24,0.6)] via-transparent to-transparent" />
        <div className="absolute bottom-10 left-10 right-10 text-white">
          <div className="font-serif text-[28px] leading-tight">“Clean home, happy paws — every time.”</div>
          <div className="mt-3 text-[12px] uppercase tracking-[0.18em] text-[var(--green-pale)]">Pawfect &amp; Pristine · Decatur · East Atlanta</div>
        </div>
      </div>
    </div>
  );
}
