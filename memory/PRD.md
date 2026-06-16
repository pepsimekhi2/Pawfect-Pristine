# Pawfect & Pristine — PRD

## Original problem statement
> "im tryna build soemthing. make me better with more animations and design. no built in drop downs and all that. i also tried to calulate eta"

User uploaded a static HTML landing page (`pawfect-and-pristine.html`) for a local Decatur / East Atlanta home cleaning + pet care business. Asked for a React rebuild with playful animations, fully custom UI (no native dropdowns), and a working ETA calculator.

## User personas
- **Local Atlanta resident** browsing for trustworthy home cleaning / pet care.
- **Pet parent / dog mom** evaluating in-home pet services while away on a trip.
- **Business owner (Pawfect)** who receives booking SMS notifications and follows up.

## Architecture
- **Frontend**: React 19 (CRA + craco), Tailwind 3, Framer Motion 11, lucide-react.
- **Backend**: FastAPI on port 8001 with `/api` prefix; MongoDB via Motor for booking persistence.
- **Integrations**:
  - **Twilio SMS** — sends a notification text to the owner on each booking. Trial account → may fail silently to unverified recipients; booking is always persisted regardless.
  - **OpenStreetMap Nominatim** — free geocoding of customer addresses.
  - **OSRM (public demo server)** — free driving distance + duration from base (Decatur, GA 33.7748,-84.2963) to customer.
- **Service zones** classified at `/api/eta`: 0–7 mi standard · 7–13 mi +$20 travel · >13 mi out-of-range (call CTA → (470) 381-4682).

## Core requirements (static)
- Distinctive, playful, hand-crafted aesthetic — no AI-slop.
- Custom UI primitives: SegmentedControl, PillToggle, Stepper (NO native `<select>`, `<input type=radio>`, etc.).
- Real driving ETA based on user address, classified into service zones.
- Multi-step booking flow that submits to backend and notifies owner.

## What's been implemented (2026-06-16)
- **Backend** (`/app/backend/server.py`)
  - `POST /api/eta` → geocode + route + zone classification + arrival window.
  - `POST /api/bookings` → persists to MongoDB, computes ETA, sends Twilio SMS to owner.
  - `GET /api/bookings/recent` → list recent bookings.
- **Frontend (v2 — green editorial restyle, kept on user request)**
  - **Palette**: deep forest green (`#1e3a2f` / `#3d7a5c`), green-light (`#eef7f2`), cream `#fdf9f5`, gold stars.
  - **Typography**: Playfair Display (serif, italic-green emphasis) + Inter (body / UI).
  - Sticky white nav with "Pawfect & Pristine · HOME & PET SERVICES" logo block.
  - 2-column Hero: gradient panel with eyebrow/title/sub/CTAs + full-bleed dog image with floating "Locally owned" badge.
  - Service strip (dot-separated) under hero.
  - 8-card Services grid with green/warm icon bubbles + Home/Pet tags.
  - Split section: Clean home image ↔ benefits checklist with green check pills.
  - 3-image Pet block (Dog Walking / Pet Sitting / Playtime) with hover zoom.
  - Stats band on green-light background.
  - **ETA Calculator** card with green-light result stats, refined zone badge (✓ standard / ⚠ extended / ✕ out-of-range with call CTA).
  - 3-card testimonial grid (light green cards, gold stars, initials avatar).
  - Multi-step booking form with thin green progress bar, refined steppers, success state with subtle confetti in brand colors.
  - Dark-green footer (`#0f2018`) with 4 columns.
- **Custom UI kit** (`components/ui-kit.jsx`) — refined SegmentedControl (green pill), PillToggle (green-light selected), Stepper (− white / + green), Primary/Outline/Ghost buttons.
- Verified by testing subagent (8/8 backend pytest, frontend smoke + integration). Critical pet-step-2 bug found and fixed (removed AnimatePresence `mode="wait"`).

## Configuration / env
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` (+14047503446)
- `OWNER_PHONE` (+14703814682) — booking SMS destination
- `ORIGIN_LAT` / `ORIGIN_LON` / `ORIGIN_LABEL` — Decatur, GA base

## Prioritized backlog
- **P0** — none open
- **P1**
  - Add a real `<input type="date">` replacement (custom calendar picker matching design).
  - Verify Twilio recipient & upgrade account (currently trial: SMS to unverified numbers will fail; bookings still persist).
  - Server-side validation of phone format (E.164).
- **P2**
  - Lifespan handler replacing deprecated `@app.on_event("shutdown")`.
  - DST-aware time math in `format_arrival` (currently fixed -5h offset).
  - Admin view of `bookings/recent` for the owner.
  - Map preview of the driving route in ETA result.
  - Repeat-customer remember-me (cookie for name/phone/address).


---

## v1.1 — Customer accounts, dashboard, Firebase mirror (2026-06-16)

### Added
- **Customer auth UI** (`/login`, `/signup`) — email + password against the existing
  JWT/bcrypt FastAPI auth. Split-hero layout with the brand bulldog.
- **Customer dashboard** at `/dashboard` (route-protected via `RequireAuth`):
  - Month calendar (custom, no external lib) with green dots for booked days and
    a click-to-reveal day detail panel.
  - "Next visit" callout card, upcoming list with status + payment pills, and
    a per-booking cancel control.
- **Refactored 5-step Book flow** (`/book`) using:
  - service + per-service tier picker (e.g. "How messy is the space?" for
    cleaning/organizing; "Walk length" for dog walking).
  - **Custom CalendarPicker + TimePicker** components (no react-day-picker).
  - Payment plan (`pay_later` / `half_now` / `all_now`) + method (`card` /
    `cash`). Cash is gated to `pay_later` only.
  - Mock card form (Stripe coming later).
  - TOS checkbox + cross-link.
- **Terms of Service** — `backend/tos.py` and a `/tos` page at the frontend.
  `GET /api/tos` returns `{ version, effective, text }`. Includes 24hr / 50%
  cancellation rule, pet liability, key handling, no-show 100%, etc.
- **Firebase RTDB mirror** — `backend/firebase_sync.py` PUT-mirrors `users/{uid}`,
  `bookings/{id}`, and `user_bookings/{uid}/{bookingId}` via REST API. No admin
  SDK — writes are unauthenticated and rely on the user pasting the rules in
  `FIREBASE_RULES.md`. All errors are swallowed (MongoDB stays authoritative).
- **New endpoints:** `GET /api/bookings/upcoming`, `POST /api/bookings/{id}/cancel`,
  `GET /api/tos`, `GET /api/firebase/status`.

### Open
- Stripe / real "Pay NOW" tap-to-pay is **MOCKED** awaiting publishable + secret keys.
- Firebase Admin SDK service-account integration is open — when added, rules can be
  tightened to per-user auth.uid validation (template provided).


---

## v1.3 — Admin passphrase, service durations, free SMS (2026-02-14)

### Added
- **Admin "magic word" gate** (`/admin`) — typing the passphrase **`duck`**
  (env `ADMIN_PASSPHRASE`) on the gate page swaps the session into the seeded
  admin JWT via `POST /api/auth/admin-passphrase`. Brute-force protected with
  the same 5-attempt / 15-min lockout that login uses.
- **Service-based time blocking** — each tier in `pricing.py` now has a
  `duration` (minutes). The booking calendar auto-greys all 30-min slots that
  would overlap an existing booking, AND all slots whose duration would push
  past the 18:30 close (with a 30-min grace). The catalog API surfaces
  `duration` so the frontend shows "~X min service" on step 2.
- **Free SMS workaround for "I'm on the way"** — admin button hits
  `POST /api/admin/bookings/{id}/notify-otw`. If Twilio is unconfigured, the
  endpoint returns a fully URL-encoded `sms:` deeplink that the AdminPage
  triggers via a hidden anchor click — this opens the device's native Messages
  app on mobile/desktop with the recipient + body pre-filled. **Zero cost.**

### Technical
- `get_service_duration(service, tier)` helper in `pricing.py` + `hhmm_to_minutes`
  / `window_minutes` utilities.
- `get_blocked_minutes_for_date(date, exclude_booking_id?)` + `slot_conflicts()`
  centralize overlap math used by `/api/availability`, booking create, and admin
  reschedule.
- Booking documents now store `duration_minutes` for stable reschedule math.
- `/api/availability` accepts optional `?service=&tier=` and returns
  `{ time, taken, too_late }` per slot.
- Fixed a latent tz-naive/tz-aware datetime comparison bug in
  `check_brute_force` that surfaced once admin-passphrase locked out — now
  normalizes Mongo's naive datetimes to UTC on read.

### Open / Backlog
- **P1** — Twilio Account SID/Auth Token/From number (user opted out for now;
  free sms: deeplink fallback in place).
- **P1** — Firebase database rules in `FIREBASE_RULES.md` need to be pasted
  into the Firebase console.
- **P1** — Stripe Payment Element for real "Pay NOW" (still MOCKED).
- **P2** — Brute-force identifier should use `X-Forwarded-For` so lockout state
  is consolidated across pod replicas (today: per-pod ingress IP).
- **P2** — Split `server.py` (~830 lines) into routers (`auth.py`, `bookings.py`,
  `admin.py`) and a `services/` module for helpers.


---

## v1.4 — PayPal Hosted Button + strict prepayment guidelines (2026-02-14)

### Added
- **PayPal Hosted Button** (merchant: Pawfect & Pristine, button id
  `NH6XJFN6LK8E2`) embedded on booking step 4 when the customer picks
  "Pay half now via PayPal" or "Pay in full now via PayPal". The button is
  rendered through `frontend/src/components/PayPalHostedButton.jsx`, which
  lazily loads PayPal's JS SDK (`hosted-buttons` + `venmo` funding, USD).
  Customer enters the amount inside PayPal's flow → money lands in the
  merchant's PayPal Business immediately.
- **PaymentGuidelines component** — large green `$amount` callout + five
  plain-English rules (exact amount, no-pay = no-service & police involvement,
  chargebacks = fraud, overpay refund, no post-completion refunds). The PayPal
  button is gated behind a required acknowledgement checkbox.
- **Two-step pay confirmation** — after PayPal, user taps
  "I've sent $X via PayPal" which advances the booking to step 5.
- **Backend additions**:
  - `payment_method` Literal extended with `"paypal"`.
  - `payment_status` set to `paid_full_pending_verify` or
    `paid_half_pending_verify` when method is PayPal (admin must verify by
    cross-checking PayPal Business inbox).
  - Owner-SMS body adapts to PayPal payments.
- **Frontend env vars** (in `frontend/.env`):
  - `REACT_APP_PAYPAL_CLIENT_ID`
  - `REACT_APP_PAYPAL_HOSTED_BUTTON_ID`

### Removed
- Mock card form (Stripe placeholder) — replaced by PayPal Hosted Button.

### Limitations / Open
- PayPal Hosted Button does NOT post back to our server, so the booking is
  flagged "pending verify" rather than auto-confirmed. Admin manually verifies
  against PayPal transactions and (future) flips to `paid_full` / `paid_half`.
- A future enhancement could swap to PayPal Smart Buttons + Orders API
  (requires Client Secret + webhook listener) for automatic capture
  confirmation.
