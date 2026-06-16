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
