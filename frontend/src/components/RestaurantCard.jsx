import React, { useState } from "react";
import { saveRestaurant, unsaveRestaurant } from "../api/restaurants";

const PRICE = { 1: "$", 2: "$$", 3: "$$$", 4: "$$$$" };
const DISCOUNT_COLOR = {
  percentage: "#d4edda",
  fixed: "#d1ecf1",
  free_item: "#fff3cd",
  special_menu: "#e2d9f3",
};
const DISCOUNT_LABEL = {
  percentage: "% OFF",
  fixed: "$ OFF",
  free_item: "FREE ITEM",
  special_menu: "STUDENT DEAL",
};

export default function RestaurantCard({ restaurant, isSaved = false, onSaveToggle }) {
  const [saved, setSaved] = useState(isSaved);
  const [loading, setLoading] = useState(false);

  async function handleSave() {
    setLoading(true);
    try {
      if (saved) {
        await unsaveRestaurant(restaurant.id);
        setSaved(false);
      } else {
        await saveRestaurant(restaurant.id);
        setSaved(true);
      }
      onSaveToggle?.();
    } catch (e) {
      // 409 = already saved, treat as saved
      if (e.response?.status === 409) setSaved(true);
    } finally {
      setLoading(false);
    }
  }

  const discountBg = DISCOUNT_COLOR[restaurant.discount_type] || "#f8f9fa";

  return (
    <div style={s.card}>
      {/* Header row */}
      <div style={s.header}>
        <div>
          <h3 style={s.name}>{restaurant.name}</h3>
          <span style={s.meta}>
            {restaurant.cuisine_type || "Restaurant"} ·{" "}
            <span style={s.price}>{PRICE[restaurant.price_range] || "?"}</span>
          </span>
        </div>
        <div style={s.badges}>
          {restaurant.is_verified && (
            <span style={s.verifiedBadge}>✓ Verified</span>
          )}
          {restaurant.discount_type && (
            <span style={{ ...s.discountBadge, background: discountBg }}>
              {DISCOUNT_LABEL[restaurant.discount_type]}
            </span>
          )}
        </div>
      </div>

      {/* Discount highlight */}
      {restaurant.discount_details && (
        <div style={s.discountBox}>
          <span style={s.discountIcon}>🎓</span>
          <span style={s.discountText}>{restaurant.discount_details}</span>
        </div>
      )}

      {/* Conditions */}
      {restaurant.discount_conditions && (
        <p style={s.conditions}>{restaurant.discount_conditions}</p>
      )}

      {/* Footer */}
      <div style={s.footer}>
        <span style={s.address}>📍 {restaurant.address}</span>
        <button
          style={{ ...s.saveBtn, ...(saved ? s.saveBtnActive : {}) }}
          onClick={handleSave}
          disabled={loading}
        >
          {saved ? "♥ Saved" : "♡ Save"}
        </button>
      </div>
    </div>
  );
}

const s = {
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "18px 20px",
    marginBottom: 14,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    border: "1px solid #f0f0f0",
    transition: "box-shadow 0.2s",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 10,
  },
  name: { margin: 0, fontSize: 17, fontWeight: 700, color: "#111" },
  meta: { fontSize: 13, color: "#888", marginTop: 2 },
  price: { color: "#57068c", fontWeight: 600 },
  badges: { display: "flex", gap: 6, flexShrink: 0, marginLeft: 12 },
  verifiedBadge: {
    background: "#e8f5e9",
    color: "#2e7d32",
    borderRadius: 20,
    padding: "3px 10px",
    fontSize: 11,
    fontWeight: 700,
  },
  discountBadge: {
    borderRadius: 20,
    padding: "3px 10px",
    fontSize: 11,
    fontWeight: 700,
    color: "#333",
  },
  discountBox: {
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
    background: "#faf5ff",
    border: "1px solid #e9d5ff",
    borderRadius: 8,
    padding: "10px 12px",
    marginBottom: 8,
  },
  discountIcon: { fontSize: 16, flexShrink: 0 },
  discountText: { fontSize: 14, color: "#4c1d95", fontWeight: 500, lineHeight: 1.4 },
  conditions: {
    fontSize: 12,
    color: "#999",
    margin: "0 0 10px",
    lineHeight: 1.5,
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 10,
    paddingTop: 10,
    borderTop: "1px solid #f5f5f5",
  },
  address: { fontSize: 12, color: "#aaa" },
  saveBtn: {
    background: "none",
    border: "1px solid #ddd",
    borderRadius: 20,
    padding: "5px 16px",
    cursor: "pointer",
    fontSize: 13,
    color: "#666",
    transition: "all 0.15s",
  },
  saveBtnActive: {
    background: "#fdf4ff",
    borderColor: "#57068c",
    color: "#57068c",
    fontWeight: 600,
  },
};
