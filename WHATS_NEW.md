# Pawfect & Pristine — v1.6 release notes

## 💳 On-site card payments (real money, no redirect)
Replaced the old "open PayPal in a new tab" hosted button with **on-site card processing** using PayPal's Orders v2 API.

- Customer enters card number / expiry / CVV / postal **inside PayPal's secure card-fields iframes** on our checkout page (no PCI burden on us, no leaving the site).
- PayPal & Venmo wallet buttons rendered alongside the card form.
- New backend endpoints:
  - `GET /api/paypal/config` — returns client_id + env for the frontend SDK loader.
  - `POST /api/paypal/create-order` — creates a PayPal order with the booking amount.
  - `POST /api/paypal/capture-order` — captures the payment and returns confirmation.
- Booking now stores `paypal_order_id`, `paypal_capture_id`, `paypal_captured_amount`.
- `payment_status` is set to **`paid_full`** / **`paid_half`** automatically on capture — no more "pending verification" for card payments.

## 📧 Transactional emails (Resend)
- `RESEND_API_KEY` wired into `backend/.env` (verified domain `pawfectpristine.xyz`, from `bookings@pawfectpristine.xyz`).
- **Signup welcome email** — branded 25%-off first-booking offer.
- **Booking confirmation email** — sent to the customer with full recap, total, paid amount, and a "back to dashboard" link.
- **Owner notification** — every booking emails `hello@pawfectpristine.com` with customer/contact/payment/PayPal-order-id, with the customer's email set as the reply-to.

## 📱 Mobile cleanup
- Killed horizontal scroll on small screens.
- Hero, section headings, plan cards, calendar tap targets all retuned for ≤ 640 px.
- iOS Safari no longer zooms in on input focus (`pp-input` font-size locked to 16 px on mobile).
- Sticky CTA bar in booking flow nav.
- iOS safe-area bottom padding.

## 🚮 Removed
- **Twilio integration** removed entirely. The "I'm on the way" admin button still works — it now hands the device a `sms:` deeplink that opens the native Messages app pre-filled (zero cost).
- **PayPal Hosted Button** component removed.

## 🛠 Make-it-runnable
- `backend/.env` + `frontend/.env` are now part of the repo (Mongo URL, admin seed, PayPal creds, Resend key, geocoder origin, JWT secret).
- `requirements.txt` cleaned of `twilio`.
- Restored real **DashboardPage** (was accidentally clobbered by a copy of BookPage in a prior commit).

## ✅ Tested
14 / 14 backend tests passed (PayPal Orders v2 against live API, payment_status logic for paid_full / paid_half / pending_verify / unpaid, plus regression on auth / catalog / quote / eta / tos / bookings / firebase).

## ⚙️ Config reference
```env
# backend/.env
RESEND_API_KEY=re_…
RESEND_FROM=Pawfect & Pristine <bookings@pawfectpristine.xyz>
OWNER_EMAIL=hello@pawfectpristine.com
PAYPAL_ENV=live
PAYPAL_CLIENT_ID=BAA…
PAYPAL_CLIENT_SECRET=ED5…

# frontend/.env
REACT_APP_BACKEND_URL=https://…
REACT_APP_PAYPAL_CLIENT_ID=BAA…
```
