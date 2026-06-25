import React, { useEffect, useMemo, useState } from "react";
import {
  PayPalScriptProvider,
  PayPalButtons,
  PayPalCardFieldsProvider,
  PayPalCardFieldsForm,
  usePayPalCardFields,
} from "@paypal/react-paypal-js";
import { CheckCircle2, Loader2, CreditCard, Wallet } from "lucide-react";
import api from "../lib/api";

/**
 * PayPalPayment — on-site card form + PayPal/Venmo wallet buttons.
 *
 * Props:
 *   amount: number (USD), required
 *   bookingRef: string, optional reference passed to PayPal
 *   onCaptured: ({ orderId, captureId, amount }) => void
 *
 * Renders:
 *   - PayPal / Venmo wallet buttons (no redirect popup for many flows)
 *   - "Or pay with card" inline form (PayPal secure card-fields iframes)
 */
export default function PayPalPayment({ amount, bookingRef, onCaptured, testid = "paypal-payment" }) {
  const [clientId, setClientId] = useState(null);
  const [configError, setConfigError] = useState("");
  const [captureState, setCaptureState] = useState("idle"); // idle | working | done | error
  const [captureError, setCaptureError] = useState("");
  const [captured, setCaptured] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/api/paypal/config")
      .then((r) => {
        if (!mounted) return;
        if (!r.data?.enabled || !r.data?.client_id) {
          setConfigError("Online payments are temporarily unavailable. Pick 'Pay on arrival' instead.");
          return;
        }
        setClientId(r.data.client_id);
      })
      .catch(() => setConfigError("Couldn’t connect to payment service. Check connection and retry."));
    return () => { mounted = false; };
  }, []);

  const sdkOptions = useMemo(() => ({
    "client-id": clientId,
    currency: "USD",
    intent: "capture",
    components: "buttons,card-fields",
    "enable-funding": "venmo,paylater",
    "disable-funding": "credit",
  }), [clientId]);

  const createOrder = async () => {
    try {
      const { data } = await api.post("/api/paypal/create-order", {
        amount: Number(amount),
        currency: "USD",
        booking_ref: bookingRef || undefined,
        description: "Pawfect & Pristine booking",
      });
      if (!data?.id) throw new Error("No order id returned");
      return data.id;
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Could not start payment.";
      setCaptureError(msg);
      setCaptureState("error");
      throw e;
    }
  };

  const captureOrder = async (orderId) => {
    setCaptureState("working");
    setCaptureError("");
    try {
      const { data } = await api.post("/api/paypal/capture-order", { order_id: orderId });
      if (data?.status !== "COMPLETED") {
        throw new Error(`Payment status: ${data?.status || "unknown"}`);
      }
      setCaptured(data);
      setCaptureState("done");
      onCaptured?.({
        orderId: data.id,
        captureId: data.capture_id,
        amount: data.captured_amount ?? Number(amount),
      });
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Couldn’t complete payment.";
      setCaptureError(msg);
      setCaptureState("error");
    }
  };

  if (configError) {
    return (
      <div className="auth-error" data-testid={`${testid}-config-error`}>{configError}</div>
    );
  }
  if (!clientId) {
    return (
      <div className="text-[13px] text-[var(--text-muted)] flex items-center gap-2" data-testid={`${testid}-loading`}>
        <Loader2 size={14} className="animate-spin" /> Loading secure payment…
      </div>
    );
  }
  if (captureState === "done" && captured) {
    return (
      <div className="payment-success" data-testid={`${testid}-success`}>
        <CheckCircle2 size={22} className="text-[var(--green)]" />
        <div>
          <div className="font-semibold text-[14px] text-[var(--text)]">
            ${(captured.captured_amount ?? amount).toFixed?.(2) || captured.captured_amount} captured.
          </div>
          <div className="text-[12px] text-[var(--text-muted)] mt-0.5">
            Confirmation #{captured.capture_id || captured.id} · keep this for your records.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid={testid}>
      <PayPalScriptProvider options={sdkOptions} deferLoading={false}>
        <div className="space-y-4">
          {/* Wallet buttons (PayPal, Venmo, Pay Later) */}
          <div data-testid={`${testid}-wallets`}>
            <div className="pp-pay-section-label">
              <Wallet size={14} /> Pay with PayPal or Venmo
            </div>
            <PayPalButtons
              style={{ layout: "vertical", shape: "rect", label: "pay", height: 44 }}
              createOrder={createOrder}
              onApprove={(data) => captureOrder(data.orderID)}
              onError={(err) => {
                setCaptureError(err?.message || "PayPal had an issue. Try the card form below.");
                setCaptureState("error");
              }}
            />
          </div>

          {/* Divider */}
          <div className="pp-pay-divider">
            <span>or</span>
          </div>

          {/* Card-fields */}
          <div data-testid={`${testid}-card`}>
            <div className="pp-pay-section-label">
              <CreditCard size={14} /> Pay with debit or credit card
            </div>
            <PayPalCardFieldsProvider
              createOrder={createOrder}
              onApprove={(data) => captureOrder(data.orderID)}
              onError={(err) => {
                const msg = err?.message || "Couldn’t process that card. Double-check details and retry.";
                setCaptureError(msg);
                setCaptureState("error");
              }}
              style={{
                input: {
                  "font-size": "15px",
                  "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  color: "#1f2a24",
                  padding: "12px",
                },
                ".invalid": { color: "#c0392b" },
              }}
            >
              <PayPalCardFieldsForm />
              <CardSubmit
                amount={amount}
                working={captureState === "working"}
                error={captureError}
                onError={(msg) => { setCaptureError(msg); setCaptureState("error"); }}
              />
            </PayPalCardFieldsProvider>
          </div>

          {captureError && (
            <div className="auth-error" data-testid={`${testid}-error`}>{captureError}</div>
          )}
        </div>
      </PayPalScriptProvider>
    </div>
  );
}

function CardSubmit({ amount, working, error, onError }) {
  const { cardFieldsForm } = usePayPalCardFields();
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!cardFieldsForm) return;
    setBusy(true);
    try {
      const state = await cardFieldsForm.getState();
      if (!state?.isFormValid) {
        onError?.("Please fill out all card fields correctly.");
        return;
      }
      await cardFieldsForm.submit();
      // PayPalCardFieldsProvider will call onApprove → captureOrder for us
    } catch (e) {
      onError?.(e?.message || "Card was declined. Try a different card.");
    } finally {
      setBusy(false);
    }
  };

  const disabled = busy || working;
  return (
    <button
      type="button"
      onClick={submit}
      disabled={disabled}
      data-testid="paypal-card-submit"
      className="paypal-card-submit"
    >
      {disabled ? (
        <><Loader2 size={16} className="animate-spin" /> Processing…</>
      ) : (
        <><CreditCard size={16} /> Pay ${Number(amount || 0).toFixed(2)} securely</>
      )}
    </button>
  );
}
