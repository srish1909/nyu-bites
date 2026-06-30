import React, { useState, useRef, useLayoutEffect } from "react";
import { saveRestaurant, unsaveRestaurant } from "../api/restaurants";

const PRICE = { 1: "$", 2: "$$", 3: "$$$", 4: "$$$$" };

const DISCOUNT_STYLE = {
  percentage:   { bg: "#f0fdf4", border: "#bbf7d0", text: "#15803d", label: "% OFF" },
  fixed:        { bg: "#eff6ff", border: "#bfdbfe", text: "#1d4ed8", label: "$ OFF" },
  free_item:    { bg: "#fffbeb", border: "#fde68a", text: "#b45309", label: "FREE ITEM" },
  special_menu: { bg: "#faf5ff", border: "#e9d5ff", text: "#7e22ce", label: "STUDENT MENU" },
};

const CUISINE_COLORS = {
  Pizza: "#ef4444", Sushi: "#3b82f6", Burgers: "#f97316", Mexican: "#eab308",
  Chinese: "#ef4444", Indian: "#f97316", Italian: "#22c55e", Thai: "#8b5cf6",
  Mediterranean: "#06b6d4", Cafe: "#78716c", Coffee: "#78716c",
  "Middle Eastern": "#f59e0b", American: "#3b82f6", Falafel: "#84cc16",
  Bagels: "#f97316", default: "#57068c",
};

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

function mapsUrl(address, lat, lng) {
  if (lat && lng) return `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
}

export default function RestaurantCard({ restaurant: r, isSaved = false, onSaveToggle, userLocation }) {
  const [saved, setSaved] = useState(isSaved);
  const [savingLoad, setSavingLoad] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const [sceneHeight, setSceneHeight] = useState("auto");
  const frontRef = useRef(null);
  const backRef = useRef(null);

  useLayoutEffect(() => {
    if (frontRef.current && backRef.current) {
      const h = Math.max(frontRef.current.offsetHeight, backRef.current.offsetHeight);
      setSceneHeight(h);
    }
  }, []);

  async function handleSave(e) {
    e.stopPropagation();
    setSavingLoad(true);
    try {
      if (saved) { await unsaveRestaurant(r.id); setSaved(false); }
      else        { await saveRestaurant(r.id);   setSaved(true);  }
      onSaveToggle?.();
    } catch (e) {
      if (e.response?.status === 409) setSaved(true);
    } finally { setSavingLoad(false); }
  }

  const ds = DISCOUNT_STYLE[r.discount_type] || null;
  const color = CUISINE_COLORS[r.cuisine_type] || CUISINE_COLORS.default;
  const mapUrl = mapsUrl(r.address, r.latitude, r.longitude);

  let distText = null;
  if (userLocation && r.latitude && r.longitude) {
    const km = haversineKm(userLocation.lat, userLocation.lng, r.latitude, r.longitude);
    distText = km < 1 ? `${Math.round(km * 1000)} m away` : `${km.toFixed(1)} km away`;
  }

  return (
    <div style={{ ...s.scene, height: sceneHeight }} onClick={() => setFlipped(f => !f)} title="Click to flip">

      <div style={{ ...s.card, transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)" }}>

        {/* ─── FRONT ─── */}
        <div ref={frontRef} style={s.face}>
          {/* Gradient header */}
          <div style={{ ...s.cardHeader, background: `linear-gradient(135deg, ${color}22, ${color}08)`, borderBottom: `3px solid ${color}` }}>
            <div style={s.cardHeaderInner}>
              <div style={s.cuisineEmoji}>{getCuisineEmoji(r.cuisine_type)}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={s.name}>{r.name}</h3>
                <div style={s.metaRow}>
                  <span style={{ ...s.cuisinePill, background: color + "20", color }}>
                    {r.cuisine_type || "Restaurant"}
                  </span>
                  <span style={{ ...s.pricePill }}>{PRICE[r.price_range] || "?"}</span>
                  {r.is_verified && <span style={s.verifiedBadge}>✓ Verified</span>}
                </div>
              </div>
              <button
                style={{ ...s.saveBtn, ...(saved ? s.saveBtnOn : {}) }}
                onClick={handleSave}
                disabled={savingLoad}
                title={saved ? "Remove from saved" : "Save"}
              >
                {saved ? "♥" : "♡"}
              </button>
            </div>
          </div>

          <div style={s.cardBody}>
            {/* Distance chip */}
            {distText && (
              <div style={s.distChip}>
                <span style={{ color }}>●</span> {distText}
              </div>
            )}

            {/* Discount banner */}
            {ds && r.discount_details && (
              <div style={{ ...s.discountBanner, background: ds.bg, borderLeft: `4px solid ${ds.text}` }}>
                <span style={{ ...s.discountBadge, background: ds.text }}>{ds.label}</span>
                <span style={{ ...s.discountDetail, color: ds.text }}>{r.discount_details}</span>
              </div>
            )}

            {/* Address with Maps link */}
            <a
              href={mapUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              style={s.addressLink}
            >
              <span style={s.pinIcon}>📍</span>
              <span style={s.addressText}>{r.address}</span>
              <span style={s.mapsBadge}>Maps ↗</span>
            </a>

            {/* Flip hint */}
            <div style={s.flipHint}>
              <span style={{ color }}>↻</span> Tap card for full details
            </div>
          </div>
        </div>

        {/* ─── BACK ─── */}
        <div ref={backRef} style={{ ...s.face, ...s.backFace }}>
          <div style={{ ...s.cardHeader, background: `linear-gradient(135deg, ${color}22, ${color}08)`, borderBottom: `3px solid ${color}` }}>
            <div style={s.cardHeaderInner}>
              <div style={s.cuisineEmoji}>{getCuisineEmoji(r.cuisine_type)}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={s.name}>{r.name}</h3>
                <span style={s.backSubtitle}>Full details</span>
              </div>
              <span style={{ ...s.closeHint, color }}>✕ close</span>
            </div>
          </div>

          <div style={s.cardBody}>

            {r.discount_details && (
              <div style={s.detailRow}>
                <div style={{ ...s.detailLabel, color }}>STUDENT DEAL</div>
                <div style={s.detailValue}>{r.discount_details}</div>
              </div>
            )}

            {r.discount_conditions && (
              <div style={s.detailRow}>
                <div style={s.detailLabel}>CONDITIONS</div>
                <div style={s.detailValue}>{r.discount_conditions}</div>
              </div>
            )}

            {r.phone && (
              <div style={s.detailRow}>
                <div style={s.detailLabel}>PHONE</div>
                <a
                  href={`tel:${r.phone}`}
                  onClick={e => e.stopPropagation()}
                  style={{ ...s.detailValue, ...s.inlineLink }}
                >
                  📞 {r.phone}
                </a>
              </div>
            )}

            {r.website && (
              <div style={s.detailRow}>
                <div style={s.detailLabel}>WEBSITE</div>
                <a
                  href={r.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={e => e.stopPropagation()}
                  style={{ ...s.detailValue, ...s.inlineLink }}
                >
                  🌐 {r.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                </a>
              </div>
            )}

            <a
              href={mapUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              style={{ ...s.mapsBtn, background: color }}
            >
              🗺 Open in Google Maps
            </a>
          </div>
        </div>

      </div>
    </div>
  );
}

function getCuisineEmoji(cuisine) {
  const map = {
    Pizza: "🍕", Sushi: "🍣", Burgers: "🍔", Mexican: "🌮", Chinese: "🥡",
    Indian: "🍛", Italian: "🍝", Thai: "🍜", Mediterranean: "🫒",
    Cafe: "☕", Coffee: "☕", "Middle Eastern": "🧆", American: "🍔",
    Falafel: "🧆", Bagels: "🥯",
  };
  return map[cuisine] || "🍽";
}

const s = {
  /* ── Flip container ─────────────────────────────── */
  scene: {
    perspective: 1200,
    marginBottom: 16,
    cursor: "pointer",
    position: "relative",
  },
  card: {
    position: "relative",
    transformStyle: "preserve-3d",
    WebkitTransformStyle: "preserve-3d",
    transition: "transform 0.55s cubic-bezier(0.4, 0, 0.2, 1)",
    height: "100%",
  },
  face: {
    backfaceVisibility: "hidden",
    WebkitBackfaceVisibility: "hidden",
    background: "#fff",
    borderRadius: 16,
    boxShadow: "0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)",
    border: "1px solid rgba(0,0,0,0.06)",
    overflow: "hidden",
    transition: "box-shadow 0.2s",
    height: "100%",
    boxSizing: "border-box",
  },
  backFace: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    transform: "rotateY(180deg)",
  },

  /* ── Card header ────────────────────────────────── */
  cardHeader: {
    padding: "14px 16px 12px",
  },
  cardHeaderInner: {
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  cuisineEmoji: {
    fontSize: 26,
    flexShrink: 0,
    lineHeight: 1,
  },
  name: {
    margin: "0 0 5px",
    fontSize: 16,
    fontWeight: 800,
    color: "#111",
    lineHeight: 1.2,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: 5,
    flexWrap: "wrap",
  },
  cuisinePill: {
    fontSize: 11,
    fontWeight: 700,
    padding: "2px 8px",
    borderRadius: 20,
    letterSpacing: "0.3px",
  },
  pricePill: {
    fontSize: 12,
    fontWeight: 700,
    color: "#57068c",
    background: "#faf5ff",
    padding: "2px 7px",
    borderRadius: 20,
  },
  verifiedBadge: {
    fontSize: 11,
    fontWeight: 700,
    color: "#15803d",
    background: "#f0fdf4",
    padding: "2px 7px",
    borderRadius: 20,
    border: "1px solid #bbf7d0",
  },
  saveBtn: {
    background: "#fff",
    border: "1.5px solid #e2e8f0",
    borderRadius: "50%",
    width: 34,
    height: 34,
    cursor: "pointer",
    fontSize: 17,
    color: "#cbd5e1",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    transition: "all 0.15s",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  },
  saveBtnOn: {
    borderColor: "#57068c",
    color: "#57068c",
    background: "#faf5ff",
  },

  /* ── Card body ──────────────────────────────────── */
  cardBody: {
    padding: "12px 16px 14px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  distChip: {
    fontSize: 12,
    color: "#64748b",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: 5,
  },
  discountBanner: {
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
    padding: "9px 12px",
    borderRadius: 10,
    border: "1px solid transparent",
  },
  discountBadge: {
    color: "#fff",
    fontSize: 10,
    fontWeight: 800,
    padding: "2px 6px",
    borderRadius: 4,
    letterSpacing: "0.5px",
    flexShrink: 0,
    marginTop: 1,
  },
  discountDetail: {
    fontSize: 13,
    fontWeight: 600,
    lineHeight: 1.4,
  },
  addressLink: {
    display: "flex",
    alignItems: "center",
    gap: 5,
    textDecoration: "none",
    color: "#475569",
    fontSize: 12,
    fontWeight: 500,
    padding: "7px 10px",
    borderRadius: 8,
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    transition: "background 0.15s",
  },
  pinIcon: { flexShrink: 0 },
  addressText: { flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  mapsBadge: {
    fontSize: 11,
    color: "#57068c",
    fontWeight: 700,
    background: "#faf5ff",
    padding: "2px 6px",
    borderRadius: 4,
    flexShrink: 0,
  },
  flipHint: {
    fontSize: 11,
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 2,
    fontWeight: 500,
    letterSpacing: "0.3px",
  },

  /* ── Back face ──────────────────────────────────── */
  backSubtitle: {
    fontSize: 12,
    color: "#94a3b8",
    fontWeight: 500,
  },
  closeHint: {
    fontSize: 11,
    fontWeight: 700,
    flexShrink: 0,
    opacity: 0.7,
  },
  detailRow: {
    borderBottom: "1px solid #f1f5f9",
    paddingBottom: 8,
  },
  detailLabel: {
    fontSize: 10,
    fontWeight: 800,
    color: "#94a3b8",
    letterSpacing: "0.8px",
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 13,
    color: "#1e293b",
    fontWeight: 500,
    lineHeight: 1.45,
  },
  inlineLink: {
    textDecoration: "none",
    color: "#57068c",
    fontWeight: 600,
  },
  mapsBtn: {
    display: "block",
    textAlign: "center",
    textDecoration: "none",
    color: "#fff",
    fontWeight: 700,
    fontSize: 13,
    padding: "10px 16px",
    borderRadius: 10,
    marginTop: 4,
    letterSpacing: "0.2px",
  },
};
