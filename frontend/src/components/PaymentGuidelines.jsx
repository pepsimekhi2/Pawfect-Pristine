import React, { useState } from "react";
import { AlertTriangle, ShieldAlert, ChevronDown, ChevronUp } from "lucide-react";

/**
 * PaymentGuidelines (compact)
 *
 * Slim acknowledgement panel shown above the PayPal payment widget. The
 * exhaustive policy lives in the TOS (accepted on the final step) — this
 * widget surfaces the most important rules so customers can't say they
 * weren't told.
 */
export default function PaymentGuidelines({ amount, planLabel, accepted, onChange }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="payment-guidelines-compact" data-testid="payment-guidelines">
      <div className="pg-summary">
        <div className="pg-amount-row">
          <div>
            <div className="pg-amount-label">Charging now</div>
            <div className="pg-amount-value">${amount}</div>
          </div>
          <div className="pg-plan-chip">{planLabel}</div>
        </div>

        <ul className="pg-rule-list">
          <li>
            <strong>Refunds:</strong> up to <strong>65%</strong> if cancelled 24+ hours before service.
            Inside 24 hours, no refund. Once we arrive on-site, no refund.
          </li>
          <li>
            <strong>Chargebacks on completed work = fraud.</strong> Reported to PayPal, your bank, and police.
          </li>
          {expanded && (
            <>
          <li>
            <strong>Technician&apos;s right to leave.</strong> Rudeness, harassment, intoxication, weapons,
            or anything making the tech feel unsafe → we leave, no refund, police if needed.
          </li>
          <li>
            <strong>Unhappy with the work?</strong> Tell us before we leave — we&apos;ll fix it on the spot
            at no extra charge.
          </li>
            </>
          )}
        </ul>

        <button
          type="button"
          className="pg-more-btn"
          onClick={() => setExpanded(v => !v)}
          data-testid="pg-more"
        >
          {expanded ? <><ChevronUp size={13} /> Hide details</> : <><ChevronDown size={13} /> See more rules</>}
        </button>
      </div>

      <label className="tos-row pg-checkbox" data-testid="payment-guidelines-row">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(e) => onChange(e.target.checked)}
          data-testid="payment-guidelines-checkbox"
        />
        <span>
          I agree to pay <strong>${amount}</strong> now and accept the refund + safety policy above.
          Full Terms of Service are on the next step.
        </span>
      </label>
    </div>
  );
}
