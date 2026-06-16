import React, { useEffect, useRef, useState } from "react";

const PAYPAL_CLIENT_ID = process.env.REACT_APP_PAYPAL_CLIENT_ID;
const HOSTED_BUTTON_ID = process.env.REACT_APP_PAYPAL_HOSTED_BUTTON_ID;
const SDK_SRC = `https://www.paypal.com/sdk/js?client-id=${PAYPAL_CLIENT_ID}&components=hosted-buttons&enable-funding=venmo&currency=USD`;

/**
 * PayPalHostedButton
 * Renders the merchant-configured PayPal Hosted Button (lets buyers pay via
 * PayPal balance, card, Venmo, or Pay-in-4). The amount is entered by the
 * customer inside PayPal's flow, so we display the expected amount prominently
 * above the button and require an acknowledgement upstream.
 */
export default function PayPalHostedButton({ testid = "paypal-button" }) {
  const containerRef = useRef(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const containerId = useRef(`pp-btn-${Math.random().toString(36).slice(2, 9)}`).current;

  useEffect(() => {
    let cancelled = false;

    const render = () => {
      if (cancelled) return;
      try {
        if (!window.paypal || !window.paypal.HostedButtons) {
          setStatus("error");
          return;
        }
        const node = document.getElementById(containerId);
        if (!node) return;
        node.innerHTML = ""; // wipe previous render (StrictMode double-invoke)
        window.paypal
          .HostedButtons({ hostedButtonId: HOSTED_BUTTON_ID })
          .render(`#${containerId}`);
        setStatus("ready");
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error("PayPal render failed", e);
        setStatus("error");
      }
    };

    if (!PAYPAL_CLIENT_ID || !HOSTED_BUTTON_ID) {
      setStatus("error");
      return;
    }

    // Already loaded
    if (window.paypal && window.paypal.HostedButtons) {
      render();
      return () => { cancelled = true; };
    }

    let script = document.getElementById("paypal-hosted-sdk");
    if (!script) {
      script = document.createElement("script");
      script.id = "paypal-hosted-sdk";
      script.src = SDK_SRC;
      script.async = true;
      document.body.appendChild(script);
    }
    const onLoad = () => render();
    const onError = () => setStatus("error");
    script.addEventListener("load", onLoad);
    script.addEventListener("error", onError);

    return () => {
      cancelled = true;
      script?.removeEventListener("load", onLoad);
      script?.removeEventListener("error", onError);
    };
  }, [containerId]);

  return (
    <div data-testid={testid}>
      <div id={containerId} ref={containerRef} className="min-h-[55px]" />
      {status === "loading" && (
        <div className="text-[12px] text-[var(--text-muted)] italic" data-testid={`${testid}-loading`}>
          Loading PayPal…
        </div>
      )}
      {status === "error" && (
        <div className="auth-error" data-testid={`${testid}-error`}>
          Couldn't load PayPal. Refresh the page or pick "Pay on arrival" instead.
        </div>
      )}
    </div>
  );
}
