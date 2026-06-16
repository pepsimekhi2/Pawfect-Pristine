# Pawfect & Pristine — What's New

## Customer accounts + dashboard
- **Sign up / Sign in** at `/signup` and `/login` (email + password, JWT, bcrypt).
  Try it: top-right "Sign in" button in the header.
- **Dashboard** at `/dashboard` (protected):
  - Month calendar with green dots on days that have scheduled visits.
  - "Next visit" callout card.
  - Upcoming list with **Scheduled** / **Cancelled** status pills and **Paid in full** / **Half paid** / **Pay on arrival** payment pills.
  - One-click **cancel** per booking.
  - "Schedule a new visit" CTA.

## Refactored booking flow
5 quick steps at `/book`:
1. **Service + tier** — pick Home or Pet, then service, then your messiness/size tier (with per-tier prices that update live).
2. **Date + time** — custom calendar + 30-minute time slots. **+$0.99 advance fee** badge appears automatically when ≥7 days out.
3. **Your details** — name, phone, address. Real driving distance + travel-fee preview (Google Maps Distance Matrix).
4. **Payment** — choose:
   - Plan: **Pay on arrival** · **Pay half now** · **Pay in full now**.
   - Method: **Tap-to-pay / card** · **Cash on arrival** (cash only with "pay on arrival" plan).
   - "Pay now" by card uses a **mock card form** (Stripe coming later — no real charge).
5. **Review + TOS** — line-by-line breakdown, TOS checkbox, confirm.

## Terms of Service
- Page at `/tos` linked from the footer + booking form.
- Backend endpoint `GET /api/tos` returns `{ version, effective, text }`.
- Covers: scheduling, pricing & advance fee, payment, cancellation (free >24hr, 50% within 24hr, 100% no-show), key handling, pet care/liability, photos, liability cap.

## Firebase Realtime Database mirror
- Your DB URL is wired up: `https://mekhis-creations-default-rtdb.firebaseio.com/`
- The FastAPI backend now **dual-writes** each new user + booking to your RTDB via REST.
- **Action you need to take:** open `/app/FIREBASE_RULES.md`, copy the rules JSON, and paste it into your Firebase console:
  - Firebase Console → your project → Realtime Database → Rules → Publish.
  - Until you do this, writes return `401 Unauthorized` (the backend silently skips them — MongoDB is the source of truth so the app still works perfectly).
- After you publish the rules, you'll see live data in Firebase Console under `/users`, `/bookings`, `/user_bookings/{uid}`.

## Test credentials
- Admin: `admin@pawfectpristine.com` / `Pawfect2026!`
- Sample customer (created during e2e test): `t1@example.com` / `Customer123!`
- Or just register a new account at `/signup`.

## Notes
- Stripe / real "Pay NOW" tap-to-pay is **MOCKED** for now — when you're ready, give me your Stripe publishable + secret keys and I'll wire in real Apple Pay / Google Pay / cards.
- Firebase admin SDK is **not** used because you didn't share a service-account credential. Once you do, I can switch to authenticated writes and stricter per-user rules (template is in `FIREBASE_RULES.md`).
