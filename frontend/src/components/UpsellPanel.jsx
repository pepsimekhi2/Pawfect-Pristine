import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus, Check, Tag } from "lucide-react";

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
      {/* Top row: property type + room counts side-by-side on desktop */}
      {(isHome || isPet) && (
        <div className="upsell-toprow">
          {isHome && upsells.property_types?.length > 0 && (
            <div className="flex-1">
              <SubHead>Where</SubHead>
              <div className="property-pills" data-testid="property-type-row">
                {upsells.property_types.map((pt, i) => (
                  <PillTile
                    key={pt.key}
                    selected={propertyType === pt.key}
                    onClick={() => setPropertyType(pt.key)}
                    testid={`property-${pt.key}`}
                    badge={pt.badge}
                    icon={pt.icon}
                    label={pt.label}
                    delay={i * 0.04}
                  />
                ))}
              </div>
            </div>
          )}
          {isHome && upsells.room_questions && (
            <div className="flex-1 grid grid-cols-2 gap-2.5">
              <Counter
                testid="bedrooms-counter"
                icon={upsells.room_questions.bedrooms?.icon}
                label="Bedrooms"
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
                label="Baths"
                value={bathrooms}
                setValue={setBathrooms}
                min={upsells.room_questions.bathrooms?.min ?? 1}
                max={upsells.room_questions.bathrooms?.max ?? 8}
                priceEach={upsells.room_questions.bathrooms?.price_each}
                freeUnits={upsells.room_questions.bathrooms?.free_units}
              />
            </div>
          )}
          {isPet && upsells.pet_question && (
            <div className="flex-1 max-w-xs">
              <SubHead>{upsells.pet_question.label}</SubHead>
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
            </div>
          )}
        </div>
      )}

      {/* Add-ons grid */}
      {upsells.addons?.length > 0 && (
        <div>
          <SubHead>{isHome ? "Add-ons" : "Extras"} <span className="opacity-60 normal-case font-normal text-[10.5px]">tap to add</span></SubHead>
          <div className="addons-row" data-testid="addons-grid">
            {upsells.addons.map((a, i) => {
              const sel = addons.includes(a.key);
              return (
                <CompactAddonTile
                  key={a.key}
                  selected={sel}
                  onClick={() => toggleAddon(a.key)}
                  testid={`addon-${a.key}`}
                  badge={`+$${a.price}`}
                  icon={a.icon}
                  label={a.label}
                  desc={a.desc}
                  delay={i * 0.03}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Discount + Live total — side by side on desktop */}
      <div className="upsell-bottomrow">
        {upsells.discounts?.length > 0 && (
          <div className="flex-1" data-testid="discount-grid">
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
                  <div className="text-[20px]">{d.icon}</div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-[12.5px] leading-tight">{d.label}</span>
                      <span className="discount-ribbon">−{Math.round((d.pct || 0) * 100)}%</span>
                    </div>
                    <div className="text-[10.5px] text-[var(--text-muted)] mt-0.5 leading-snug">{d.sublabel}</div>
                  </div>
                  <div className={`check-bubble ${sel ? "is-on" : ""}`}><Check size={12} strokeWidth={3} /></div>
                </motion.button>
              );
            })}
          </div>
        )}
        <AnimatePresence mode="popLayout">
          {quote && (
            <motion.div
              key={`total-${quote.total}`}
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: "spring", stiffness: 380, damping: 26 }}
              className="live-total-card"
              data-testid="live-total"
            >
              <div>
                <div className="text-[10px] uppercase tracking-[0.18em] font-semibold text-[var(--green-pale)]">Running total</div>
                <div className="font-serif text-[28px] font-bold leading-none mt-1.5">${quote.total}</div>
                {quote.discount_total > 0 && (
                  <div className="text-[10.5px] text-[var(--green-pale)] mt-1 flex items-center gap-1">
                    <Tag size={10} /> Saved ${quote.discount_total}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SubHead({ children }) {
  return (
    <div className="text-[10.5px] uppercase tracking-[0.14em] font-semibold text-[var(--text-muted)] mb-2 flex items-center gap-2">
      {children}
    </div>
  );
}

function PillTile({ selected, onClick, testid, badge, icon, label, delay = 0 }) {
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.25 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      data-testid={testid}
      className={`property-pill ${selected ? "is-selected" : ""}`}
    >
      {badge && <span className="property-badge">{badge}</span>}
      <span className="text-[15px]">{icon}</span>
      <span className="text-[12px] font-semibold">{label}</span>
    </motion.button>
  );
}

function CompactAddonTile({ selected, onClick, testid, badge, icon, label, desc, delay = 0 }) {
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.25 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      data-testid={testid}
      className={`addon-compact ${selected ? "is-selected" : ""}`}
    >
      {badge && <span className="addon-badge">{badge}</span>}
      <span className="text-[18px] mb-0.5">{icon}</span>
      <span className="font-semibold text-[12px] leading-tight">{label}</span>
      <span className="text-[10px] text-[var(--text-muted)] leading-tight mt-0.5 line-clamp-2">{desc}</span>
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
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-[15px]">{icon}</span>
          <span className="font-semibold text-[12px]">{label}</span>
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
      <div className="counter-controls w-full justify-between">
        <button type="button" onClick={dec} data-testid={`${testid}-dec`} className="counter-btn" disabled={safeValue <= min}><Minus size={12} /></button>
        <span className="counter-value" data-testid={`${testid}-value`}>{safeValue}</span>
        <button type="button" onClick={inc} data-testid={`${testid}-inc`} className="counter-btn" disabled={safeValue >= max}><Plus size={12} /></button>
      </div>
    </div>
  );
}
