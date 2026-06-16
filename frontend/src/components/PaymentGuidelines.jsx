import React from "react";
import { AlertTriangle, Check, ShieldAlert, Receipt } from "lucide-react";

/**
 * PaymentGuidelines
 * Strict, plain-language rules the customer MUST acknowledge before the
 * PayPal button renders. Displays the expected amount prominently.
 */
export default function PaymentGuidelines({ amount, planLabel, accepted, onChange }) {
  return (
    <div className="payment-guidelines" data-testid="payment-guidelines">
      {/* Amount callout — impossible to miss */}
      <div className="amount-callout" data-testid="amount-callout">
        <div className="text-[10.5px] uppercase tracking-[0.18em] font-semibold text-[var(--green-pale)]">
          Pay This Exact Amount
        </div>
        <div className="font-serif text-[44px] md:text-[52px] font-bold leading-none mt-2">
          ${amount}
        </div>
        <div className="text-[11px] font-medium text-[var(--green-pale)] mt-2 uppercase tracking-[0.14em]">
          {planLabel}
        </div>
      </div>

      <div className="guidelines-card">
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert size={18} className="text-[var(--green-dark)]" />
          <h4 className="font-serif text-[20px] text-[var(--green-dark)] leading-tight">
            Read before you pay.
          </h4>
        </div>

        <ul className="space-y-3 mt-4">
          <Rule
            icon={<Receipt size={14} />}
            head={<>Enter <strong>exactly ${amount}</strong> in PayPal.</>}
            body={<>If you underpay, the unpaid balance is due in <strong>cash</strong> when we arrive. Service won't start until it's settled.</>}
          />
          <Rule
            icon={<AlertTriangle size={14} />}
            head={<>No-pay = no-service.</>}
            body={<>Refusing to pay the balance after we arrive is theft of service. We will leave, keep any partial payment as a cancellation fee, and pursue the balance through DeKalb County small-claims court. We <strong>will</strong> involve local police if needed.</>}
          />
          <Rule
            icon={<ShieldAlert size={14} />}
            head={<>Chargebacks on completed work = fraud.</>}
            body={<>Filing a PayPal dispute or card chargeback after we've performed the agreed service is reported as fraud to PayPal and to local authorities. We document every visit with timestamped photos.</>}
          />
          <Rule
            icon={<Check size={14} />}
            head={<>Overpaid by mistake? We refund within 48 hours.</>}
            body={<>Text us at (470) 381-4682 with your booking name and we'll send the difference back to your PayPal.</>}
          />
          <Rule
            icon={<Check size={14} />}
            head={<>No refunds once service is complete.</>}
            body={<>If you're unhappy with the work, tell us before we leave — we'll fix it on the spot. Refunds outside that window aren't issued unless agreed in writing.</>}
          />
        </ul>

        <label className="tos-row mt-5" data-testid="payment-guidelines-row">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => onChange(e.target.checked)}
            data-testid="payment-guidelines-checkbox"
          />
          <span>
            I've read the rules above and agree to pay <strong>exactly ${amount}</strong> now.
            I understand the unpaid balance (if any) is due in cash on arrival, and that
            disputing a legitimate charge will be reported as fraud.
          </span>
        </label>
      </div>
    </div>
  );
}

function Rule({ icon, head, body }) {
  return (
    <li className="rule-row">
      <span className="rule-icon">{icon}</span>
      <div>
        <div className="text-[13.5px] font-semibold text-[var(--text)]">{head}</div>
        <div className="text-[12.5px] text-[var(--text-muted)] mt-0.5 leading-[1.55]">{body}</div>
      </div>
    </li>
  );
}
