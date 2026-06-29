import React, { useState } from "react";
import { saveRestaurant, unsaveRestaurant } from "../api/restaurants";

const PRICE = { 1: "$", 2: "$$", 3: "$$$", 4: "$$$$" };

const DISCOUNT_STYLE = {
  percentage: { bg: "#f0fdf4", border: "#bbf7d0", text: "#15803d", label: "% OFF" },
  fixed:      { bg: "#eff6ff", border: "#bfdbfe", text: "#1d4ed8", label: "$ OFF" },
  free_item:  { bg: "#fffbeb", border: "#fde68a", text: "#b45309", label: "FREE ITEM" },
  special_menu: { bg: "#faf5ff", border: "#e9d5ff", text: "#7e22ce", label: "STUDENT MENU" },
};

const CUISINE_COLORS = {
  Pizza: "#ef4444", Sushi: "#3b82f6", Burgers: "#f97316", Mexican: "#eab308",
  Chinese: "#ef4444", Indian: "#f97316", Italian: "#22c55e", Thai: "#8b5cf6",
  Mediterranean: "#06b6d4", Coffee: "#78716c", default: "#57068c",
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

export default function RestaurantCard({ restaurant: r, isSaved = false, onSaveToggle, userLocation }) {
  const [saved, setSaved] = useState(isSaved);
  const [loading, setLoading] = useState(false);

  async function handleSave() {
    setLoading(true);
    try {
      if (saved) {
        await unsaveRestaurant(r.id);
        setSaved(false);
      } else {
        await saveRestaurant(r.id);
        setSaved(true);
      }
      onSaveToggle?.();
    } catch (e) {
      if (e.response?.status === 409) setSaved(true);
    } finally {
      setLoading(false);
    }
  }

  const discountStyle = DISCOUNT_STYLE[r.discount_type] || null;
  const cuisineColor = CUISINE_COLORS[r.cuisine_type] || CUISINE_COLORS.default;

  let distanceText = null;
  if (userLocation && r.latitude && r.longitude) {
    const km = haversineKm(userLocation.lat, userLocation.lng, r.latitude, r.longitude);
    distanceText = km < 1 ? `${Math.round(km * 1000)}m away` : `${km.toFixed(1)}km away`;
  }

  return (
    <div style={s.card}>
      {/* Colored top accent bar by cuisine */}
      <div style={{ ...s.accentBar, background: cuisineColor }} />

      <div style={s.body}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.headerLeft}>
            <h3 style={s.name}>{r.name}</h3>
            <div style={s.metaRow}>
              <span style={{ ...s.cuisinePill, background: cuisineColor + "18", color: cuisineColor }}>
                {r.cuisine_type || "Restaurant"}
              </span>
              <span style={s.price}>{PRICE[r.price_range] || "?"}</span>
              {r.is_verified && <span style={s.verified}>✓ Verified</span>}
              {distanceText && <span style={s.distance}>📍 {distanceText}</span>}
            </div>
          </div>

          <button
            style={{ ...s.saveBtn, ...(saved ? s.saveBtnActive : {}) }}
            onClick={handleSave}
            disabled={loading}
            title={saved ? "Unsave" : "Save"}
          >
            {saved ? "♥" : "♡"}
          </button>
        </div>

        {/* Discount highlight */}
        {discountStyle && r.discount_details && (
          <div style={{ ...s.discountBox, background: discountStyle.bg, borderColor: discountStyle.border }}>
            <span style={{ ...s.discountBadge, background: discountStyle.bg, color: discountStyle.text, borderColor: discountStyle.border }}>
              {discountStyle.label}
            </span>
            <span style={{ ...s.discountText, color: discountStyle.text }}>
              {r.discount_details}
            </span>
          </div>
        )}

        {/* Conditions */}
        {r.discount_conditions && (
          <p style={s.conditions}>📋 {r.discount_conditions}</p>
        )}

        {/* Footer */}
        <div style={s.footer}>
          <span style={s.address}>📍 {r.address}</span>
        </div>
      </div>
    </div>
  );
}

const s = {
  card: {
    background: "#fff",
    borderRadius: 14,
    marginBottom: 14,
    boxShadow: "0 2px 8px rgba(0,0,0,0.07)",
    border: "1px solid #efefef",
    overflow: "hidden",
    transition: "box-shadow 0.2s",
  },
  accentBar: { height: 4, width: "100%" },
  body: { padding: "16px 18px" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 },
  headerLeft: { flex: 1, minWidth: 0 },
  name: { margin: "0 0 6px", fontSize: 17, fontWeight: 700, color: "#111", lineHeight: 1.2 },
  metaRow: { display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" },
  cuisinePill: {
    fontSize: 11,
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 20,
    letterSpacing: "0.3px",
  },
  price: { fontSize: 12, fontWeight: 700, color: "#57068c" },
  verified: {
    fontSize: 11,
    fontWeight: 700,
    color: "#15803d",
    background: "#f0fdf4",
    padding: "2px 7px",
    borderRadius: 20,
  },
  distance: { fontSize: 11, color: "#94a3b8" },
  saveBtn: {
    background: "none",
    border: "1.5px solid #e2e8f0",
    borderRadius: "50%",
    width: 36,
    height: 36,
    cursor: "pointer",
    fontSize: 18,
    color: "#cbd5e1",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginLeft: 10,
    transition: "all 0.15s",
  },
  saveBtnActive: {
    borderColor: "#57068c",
    color: "#57068c",
    background: "#faf5ff",
  },
  discountBox: {
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
    borderRadius: 8,
    border: "1px solid",
    padding: "9px 12px",
    marginBottom: 8,
  },
  discountBadge: {
    fontSize: 10,
    fontWeight: 800,
    padding: "2px 7px",
    borderRadius: 4,
    border: "1px solid",
    flexShrink: 0,
    letterSpacing: "0.5px",
    marginTop: 1,
  },
  discountText: { fontSize: 13, fontWeight: 500, lineHeight: 1.4 },
  conditions: {
    fontSize: 12,
    color: "#94a3b8",
    margin: "0 0 10px",
    lineHeight: 1.5,
  },
  footer: {
    borderTop: "1px solid #f1f5f9",
    paddingTop: 10,
    marginTop: 6,
  },
  address: { fontSize: 12, color: "#94a3b8" },
};
