import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus, Check, Sparkles, Tag } from "lucide-react";

/**
 * UpsellPanel — the per-service questionnaire. Renders conditionally based on
 * `upsells` schema (returned by /api/catalog) and updates the live quote chip.
 *
 * UX notes:
 * - All controls animate in with stagger.
 * - Selected items get a green ring + check.
 * - "−15%" discount card has a yellow ribbon.
 * - "+30%" business badge sits on the business property-type card.
 */
export default function UpsellPanel({
  svc, upsells,
  propertyType, setPropertyType,
  bedrooms, setBedrooms,
  bathrooms, setBathrooms,
  petCount, setPetCount,
  addons, setAddons,
  discounts, setDiscounts,
  quote,
}) {
  const toggleAddon = (key) =>
    setAddons((curr) => curr.includes(key) ? curr.filter((k) => k !== key) : [...curr, key]);
  const toggleDiscount = (key) =>
    setDiscounts((curr) => curr.includes(key) ? curr.filter((k) => k !== key) : [...curr, key]);

  const isHome = svc.category === "home";
  const isPet = svc.category === "pet";

  return (
    <div className="upsell-panel" data-testid="upsell-panel">
      <div className="upsell-head">
        <Sparkles size={14} className="text-[var(--green)]" />
        <span className="eyebrow !mt-0">Customize · Tap to add</span>
      </div>

      {/* Property type — cleaning only */}
      {isHome && upsells.property_types?.length > 0 && (
        <Section title="Where are we cleaning?">
          <div className="grid grid-cols-3 gap-2.5" data-testid="property-type-row">
            {upsells.property_types.map((pt, i) => (
              <Tile
                key={pt.key}
                selected={propertyType === pt.key}
                onClick={() => setPropertyType(pt.key)}
                testid={`property-${pt.key}`}
                badge={pt.badge}
                delay={i * 0.04}
              >
                <div className="text-[22px] leading-none mb-1.5">{pt.icon}</div>
                <div className="font-semibold text-[12.5px] leading-tight">{pt.label}</div>
              </Tile>
            ))}
          </div>
        </Section>
      )}

      {/* Room counts — cleaning only */}
      {isHome && upsells.room_questions && (
        <Section title="How big is the space?">
          <div className="grid grid-cols-2 gap-3" data-testid="room-counts">
            <Counter
              testid="bedrooms-counter"
              icon={upsells.room_questions.bedrooms?.icon}
              label={upsells.room_questions.bedrooms?.label}
              value={bedrooms}
              setValue={setBedrooms}
              min={upsells.room_questions.bedrooms?.min ?? 0}
              max={upsells.room_questions.bedrooms?.max ?? 10}
              priceEach={upsells.room_questions.bedrooms?.price_each}
              freeUnits={upsells.room_questions.bedrooms?.free_units}
            />
            <Counter
              testid="bathrooms-counter"
              icon={upsells.room_questions.bathrooms?.icon}
              label={upsells.room_questions.bathrooms?.label}
              value={bathrooms}
              setValue={setBathrooms}
              min={upsells.room_questions.bathrooms?.min ?? 1}
              max={upsells.room_questions.bathrooms?.max ?? 8}
              priceEach={upsells.room_questions.bathrooms?.price_each}
              freeUnits={upsells.room_questions.bathrooms?.free_units}
            />
          </div>
        </Section>
      )}

      {/* Pet count — pet services only */}
      {isPet && upsells.pet_question && (
        <Section title={upsells.pet_question.label}>
          <Counter
            testid="pet-counter"
            icon={upsells.pet_question.icon}
            label="Pets"
            value={petCount}
            setValue={setPetCount}
            min={upsells.pet_question.min ?? 1}
            max={upsells.pet_question.max ?? 8}
            priceEach={upsells.pet_question.price_each}
            freeUnits={upsells.pet_question.free_units}
          />
        </Section>
      )}

      {/* Add-ons */}
      {upsells.addons?.length > 0 && (
        <Section title={isHome ? "Add-ons" : "Extras"}>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5" data-testid="addon-grid">
            {upsells.addons.map((a, i) => {
              const sel = addons.includes(a.key);
              return (
                <Tile
                  key={a.key}
                  selected={sel}
                  onClick={() => toggleAddon(a.key)}
                  testid={`addon-${a.key}`}
                  badge={`+$${a.price}`}
                  delay={i * 0.03}
                >
                  <div className="text-[20px] leading-none mb-1">{a.icon}</div>
                  <div className="font-semibold text-[12.5px] leading-tight">{a.label}</div>
                  <div className="text-[10.5px] text-[var(--text-muted)] mt-1 leading-tight">{a.desc}</div>
                </Tile>
              );
            })}
          </div>
        </Section>
      )}

      {/* Discounts */}
      {upsells.discounts?.length > 0 && (
        <Section title="Save money">
          <div className="grid gap-2.5" data-testid="discount-grid">
            {upsells.discounts.map((d, i) => {
              const sel = discounts.includes(d.key);
              return (
                <motion.button
                  key={d.key}
                  type="button"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.28 }}
                  onClick={() => toggleDiscount(d.key)}
                  data-testid={`discount-${d.key}`}
                  className={`discount-card ${sel ? "is-selected" : ""}`}
                >
                  <div className="text-[24px]">{d.icon}</div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[14px]">{d.label}</span>
                      <span className="discount-ribbon">−{Math.round((d.pct || 0) * 100)}%</span>
                    </div>
                    <div className="text-[11.5px] text-[var(--text-muted)] mt-0.5 leading-snug">{d.sublabel}</div>
                  </div>
                  <div className={`check-bubble ${sel ? "is-on" : ""}`}><Check size={14} strokeWidth={3} /></div>
                </motion.button>
              );
            })}
          </div>
        </Section>
      )}

      {/* Live total */}
      <AnimatePresence mode="popLayout">
        {quote && (
          <motion.div
            key={`total-${quote.total}`}
            initial={{ opacity: 0, y: 10, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 380, damping: 26 }}
            className="live-total-card"
            data-testid="live-total"
          >
            <div>
              <div className="text-[10.5px] uppercase tracking-[0.18em] font-semibold text-[var(--green-pale)]">Running total</div>
              <div className="font-serif text-[34px] font-bold leading-none mt-1">${quote.total}</div>
              {quote.discount_total > 0 && (
                <div className="text-[11.5px] text-[var(--green-pale)] mt-1.5 flex items-center gap-1">
                  <Tag size={11} /> You saved ${quote.discount_total}
                </div>
              )}
            </div>
            <div className="text-right text-[10.5px] uppercase tracking-[0.14em] font-semibold text-[var(--green-pale)]">
              {quote.breakdown?.length || 0} line items
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="upsell-section">
      <div className="text-[11px] uppercase tracking-[0.14em] font-semibold text-[var(--text-muted)] mb-2.5">{title}</div>
      {children}
    </div>
  );
}

function Tile({ selected, onClick, children, badge, testid, delay = 0 }) {
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.25 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      data-testid={testid}
      className={`upsell-tile ${selected ? "is-selected" : ""}`}
    >
      {badge && <span className="upsell-badge">{badge}</span>}
      {children}
    </motion.button>
  );
}

function Counter({ testid, icon, label, value, setValue, min, max, priceEach, freeUnits }) {
  const safeValue = Math.max(min, Math.min(max, value ?? min));
  const extra = Math.max(0, safeValue - (freeUnits ?? 0));
  const extraCost = extra * (priceEach ?? 0);
  const dec = () => setValue(Math.max(min, safeValue - 1));
  const inc = () => setValue(Math.min(max, safeValue + 1));
  return (
    <div className="counter-card" data-testid={testid}>
      <div className="flex items-center gap-2.5 mb-3">
        <span className="text-[20px]">{icon}</span>
        <div>
          <div className="font-semibold text-[13px]">{label}</div>
          <div className="text-[10.5px] text-[var(--text-muted)]">
            First {freeUnits} included · +${priceEach} each after
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between gap-3">
        <div className="counter-controls">
          <button type="button" onClick={dec} data-testid={`${testid}-dec`} className="counter-btn" disabled={safeValue <= min}><Minus size={14} /></button>
          <span className="counter-value" data-testid={`${testid}-value`}>{safeValue}</span>
          <button type="button" onClick={inc} data-testid={`${testid}-inc`} className="counter-btn" disabled={safeValue >= max}><Plus size={14} /></button>
        </div>
        <AnimatePresence mode="popLayout">
          {extraCost > 0 && (
            <motion.span
              key={extraCost}
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.6 }}
              transition={{ type: "spring", stiffness: 380, damping: 22 }}
              className="counter-extra"
              data-testid={`${testid}-extra`}
            >
              +${extraCost}
            </motion.span>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
