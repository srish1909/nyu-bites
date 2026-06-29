import React, { useEffect, useState, useCallback } from "react";
import FilterBar from "../components/FilterBar";
import RestaurantCard from "../components/RestaurantCard";
import { getRestaurants, getSaved } from "../api/restaurants";

export default function Browse() {
  const [restaurants, setRestaurants] = useState([]);
  const [savedIds, setSavedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});

  const fetchSaved = useCallback(async () => {
    try {
      const data = await getSaved();
      setSavedIds(new Set(data.map((r) => r.id)));
    } catch {
      // not critical
    }
  }, []);

  const fetchRestaurants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (filters.search) params.search = filters.search;
      if (filters.cuisine_type) params.cuisine_type = filters.cuisine_type;
      if (filters.discount_type) params.discount_type = filters.discount_type;
      if (filters.open_now) params.open_now = true;
      if (filters.is_verified) params.is_verified = true;
      const data = await getRestaurants(params);
      setRestaurants(data);
    } catch {
      setError("Failed to load restaurants. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchSaved();
  }, [fetchSaved]);

  useEffect(() => {
    const t = setTimeout(fetchRestaurants, filters.search ? 350 : 0);
    return () => clearTimeout(t);
  }, [fetchRestaurants, filters]);

  return (
    <div style={s.page}>
      <FilterBar filters={filters} onChange={setFilters} />
      <div style={s.content}>
        {loading && <div style={s.status}>Loading...</div>}
        {error && <div style={{ ...s.status, color: "#c0392b" }}>{error}</div>}
        {!loading && !error && restaurants.length === 0 && (
          <div style={s.status}>No restaurants found. Try different filters.</div>
        )}
        {!loading && restaurants.map((r) => (
          <RestaurantCard
            key={r.id}
            restaurant={r}
            isSaved={savedIds.has(r.id)}
            onSaveToggle={fetchSaved}
          />
        ))}
      </div>
    </div>
  );
}

const s = {
  page: { display: "flex", flexDirection: "column", minHeight: "calc(100vh - 56px)" },
  content: { padding: "16px 24px", maxWidth: 760, margin: "0 auto", width: "100%" },
  status: { textAlign: "center", color: "#aaa", fontSize: 14, marginTop: 40 },
};
