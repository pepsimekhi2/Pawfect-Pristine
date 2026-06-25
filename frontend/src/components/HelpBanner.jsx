import React from "react";
import { Phone } from "lucide-react";

export default function HelpBanner({ phone = "(404) 750-3446", tel = "+14047503446", floating = true }) {
  const cls = floating
    ? "fixed bottom-5 right-5 z-40 bg-white shadow-[0_8px_24px_rgba(15,32,24,0.15)] border border-[var(--border)] rounded-full pl-3 pr-4 py-2 flex items-center gap-2 hover:shadow-[0_12px_32px_rgba(15,32,24,0.22)] transition-shadow"
    : "inline-flex items-center gap-2 bg-[var(--green-light)] border border-[var(--green-pale)] rounded-full px-3 py-1.5 text-[12px]";
  return (
    <a href={`tel:${tel}`} className={cls} data-testid="help-phone">
      <span className="w-7 h-7 rounded-full bg-[var(--green)] text-white flex items-center justify-center">
        <Phone size={13} strokeWidth={2.5} />
      </span>
      <span className="flex flex-col leading-tight">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--green)]">Need help?</span>
        <span className="text-[13px] font-semibold text-[var(--green-dark)]">{phone}</span>
      </span>
    </a>
  );
}
