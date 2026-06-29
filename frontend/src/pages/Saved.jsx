import React, { useEffect, useState, useCallback } from "react";
import RestaurantCard from "../components/RestaurantCard";
import { getSaved } from "../api/restaurants";

export default function Saved() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSaved();
      setRestaurants(data);
    } catch {
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return (
    <div style={s.page}>
      <div style={s.content}>
        <h2 style={s.title}>Saved Places</h2>
        {loading && <p style={s.status}>Loading...</p>}
        {!loading && restaurants.length === 0 && (
          <div style={s.empty}>
            <div style={s.emptyIcon}>♡</div>
            <p style={s.emptyText}>No saved restaurants yet.</p>
            <p style={s.emptyHint}>Browse deals and tap Save to keep track of your favorites.</p>
          </div>
        )}
        {!loading && restaurants.map((r) => (
          <RestaurantCard
            key={r.id}
            restaurant={r}
            isSaved={true}
            onSaveToggle={fetch}
          />
        ))}
      </div>
    </div>
  );
}

const s = {
  page: { minHeight: "calc(100vh - 56px)", background: "#f9f9f9" },
  content: { padding: "16px 24px", maxWidth: 760, margin: "0 auto" },
  title: { fontSize: 22, fontWeight: 700, color: "#111", marginBottom: 16 },
  status: { color: "#aaa", fontSize: 14 },
  empty: {
    textAlign: "center",
    marginTop: 60,
    color: "#bbb",
  },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 18, fontWeight: 600, color: "#aaa", margin: "0 0 8px" },
  emptyHint: { fontSize: 14, color: "#ccc" },
};
