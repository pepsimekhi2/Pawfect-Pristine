import React, { useEffect, useRef, useState } from "react";
import { MapPin, Loader2, AlertTriangle } from "lucide-react";
import api from "../lib/api";

/**
 * AddressAutocomplete
 * - As-you-type suggestions from /api/geocode/suggest (OSM-based, biased to GA).
 * - On select / blur, optionally verifies via /api/eta to surface the service-zone
 *   classification. Calls `onZone({zone, distance_miles, extra_fee})` when verified.
 * - Gracefully no-ops on suggestions if the upstream is rate-limited.
 *
 * Props:
 *   value, onChange    — controlled string
 *   onZone?            — fn called with the zone object after verify
 *   placeholder?
 *   testid?
 *   verifyOnBlur=true  — call /api/eta after select / blur
 *   disabled?
 */
export default function AddressAutocomplete({
  value,
  onChange,
  onZone,
  placeholder = "Street, City, State ZIP",
  testid = "addr-autocomplete",
  verifyOnBlur = true,
  disabled = false,
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [zone, setZoneState] = useState(null); // {zone, distance_miles, extra_fee, zone_message}
  const [verifyErr, setVerifyErr] = useState("");
  const containerRef = useRef(null);
  const debounceRef = useRef(null);
  const lastVerified = useRef("");

  // Close dropdown on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Debounced suggest
  useEffect(() => {
    if (!value || value.length < 3) {
      setSuggestions([]);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/api/geocode/suggest?q=${encodeURIComponent(value)}&limit=6`);
        setSuggestions(data?.results || []);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 350);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
  }, [value]);

  const verifyZone = async (addr) => {
    if (!addr || addr === lastVerified.current) return;
    lastVerified.current = addr;
    setVerifying(true);
    setVerifyErr("");
    try {
      const { data } = await api.post("/api/eta", { address: addr });
      const z = {
        zone: data.zone,
        zone_label: data.zone_label,
        zone_message: data.zone_message,
        distance_miles: data.distance_miles,
        extra_fee: data.extra_fee,
        resolved_address: data.resolved_address,
      };
      setZoneState(z);
      onZone?.(z);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Couldn't verify that address.";
      setVerifyErr(msg);
      setZoneState(null);
      onZone?.(null);
    } finally {
      setVerifying(false);
    }
  };

  const handleSelect = (s) => {
    onChange(s.address);
    setOpen(false);
    setSuggestions([]);
    if (verifyOnBlur) verifyZone(s.address);
  };

  const handleBlur = () => {
    // Verify after a tick so click on suggestion can fire first
    setTimeout(() => {
      if (verifyOnBlur && value && value.length > 6 && value !== lastVerified.current) {
        verifyZone(value);
      }
    }, 200);
  };

  return (
    <div className="relative" ref={containerRef} data-testid={testid}>
      <div className="relative">
        <input
          type="text"
          className="pp-input pl-9"
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
            setZoneState(null);
            setVerifyErr("");
          }}
          onFocus={() => setOpen(true)}
          onBlur={handleBlur}
          autoComplete="off"
          spellCheck={false}
          data-testid={`${testid}-input`}
        />
        <MapPin size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
        {(loading || verifying) && (
          <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] animate-spin" />
        )}
      </div>

      {open && suggestions.length > 0 && (
        <ul className="addr-suggest-list" data-testid={`${testid}-list`}>
          {suggestions.map((s, i) => (
            <li
              key={`${s.label}-${i}`}
              className="addr-suggest-item"
              data-testid={`${testid}-item-${i}`}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(s); }}
            >
              <MapPin size={13} className="text-[var(--green)] shrink-0" />
              <span className="text-[13.5px]">{s.label}</span>
            </li>
          ))}
        </ul>
      )}

      {/* Verified zone status */}
      {zone && !verifyErr && (
        <div className={`addr-zone-chip addr-zone-${zone.zone}`} data-testid={`${testid}-zone`}>
          {zone.zone === "out_of_range" ? (
            <><AlertTriangle size={13} /> Out of service area · {zone.distance_miles} mi</>
          ) : (
            <>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-current" />
              {zone.zone_label || zone.zone} · {zone.distance_miles} mi
              {zone.extra_fee > 0 ? ` · +$${zone.extra_fee} travel fee` : ""}
            </>
          )}
        </div>
      )}
      {verifyErr && (
        <div className="addr-zone-chip addr-zone-out_of_range" data-testid={`${testid}-error`}>
          <AlertTriangle size={13} /> {verifyErr}
        </div>
      )}
    </div>
  );
}
