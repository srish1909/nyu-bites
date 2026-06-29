import React, { useEffect, useState, useCallback, useRef } from "react";
import FilterBar from "../components/FilterBar";
import RestaurantCard from "../components/RestaurantCard";
import { getRestaurants, getSaved } from "../api/restaurants";

export default function Browse({ userLocation }) {
  const [restaurants, setRestaurants] = useState([]);
  const [savedIds, setSavedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});

  const location = userLocation; // passed from App (single geolocation request)
  const locationStatus = location ? "granted" : "idle";

  const fetchSaved = useCallback(async () => {
    try {
      const data = await getSaved();
      setSavedIds(new Set(data.map((r) => r.id)));
    } catch {}
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
      // Pass location so backend can sort/filter by distance
      if (location) {
        params.lat = location.lat;
        params.lng = location.lng;
      }
      const data = await getRestaurants(params);
      setRestaurants(data);
    } catch {
      setError("Failed to load restaurants. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  }, [filters, location]);

  useEffect(() => { fetchSaved(); }, [fetchSaved]);

  useEffect(() => {
    const t = setTimeout(fetchRestaurants, filters.search ? 350 : 0);
    return () => clearTimeout(t);
  }, [fetchRestaurants, filters]);

  return (
    <div style={s.page}>
      {/* Hero banner */}
      <div style={s.hero}>
        <div style={s.heroInner}>
          <h1 style={s.heroTitle}>Student Deals Near You</h1>
          <p style={s.heroSub}>
            Exclusive discounts at restaurants and cafes around NYU campus
          </p>
          {locationStatus === "granted" && (
            <div style={s.locationBadge}>
              📍 Using your location for nearby results
            </div>
          )}
          {locationStatus === "denied" && (
            <div style={{ ...s.locationBadge, background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.6)" }}>
              Enable location for distance-sorted results
            </div>
          )}
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      <div style={s.content}>
        {loading && (
          <div style={s.loadingGrid}>
            {[1,2,3].map(i => <div key={i} style={s.skeleton} />)}
          </div>
        )}
        {error && (
          <div style={s.errorBox}>
            <span style={s.errorIcon}>⚠️</span>
            <span>{error}</span>
          </div>
        )}
        {!loading && !error && restaurants.length === 0 && (
          <div style={s.empty}>
            <div style={s.emptyIcon}>🔍</div>
            <p style={s.emptyText}>No restaurants found</p>
            <p style={s.emptyHint}>Try adjusting your filters or search terms</p>
          </div>
        )}
        {!loading && !error && restaurants.length > 0 && (
          <>
            <p style={s.count}>{restaurants.length} restaurant{restaurants.length !== 1 ? "s" : ""} found</p>
            {restaurants.map((r) => (
              <RestaurantCard
                key={r.id}
                restaurant={r}
                isSaved={savedIds.has(r.id)}
                onSaveToggle={fetchSaved}
                userLocation={location}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

const s = {
  page: { display: "flex", flexDirection: "column", minHeight: "calc(100vh - 56px)", background: "#f5f4f8" },
  hero: {
    background: "linear-gradient(135deg, #3d0066 0%, #57068c 60%, #7b1fa2 100%)",
    padding: "32px 24px 28px",
  },
  heroInner: { maxWidth: 760, margin: "0 auto" },
  heroTitle: { color: "#fff", fontSize: 26, fontWeight: 800, margin: "0 0 6px", letterSpacing: "-0.5px" },
  heroSub: { color: "rgba(255,255,255,0.75)", fontSize: 14, margin: "0 0 14px" },
  locationBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    background: "rgba(255,255,255,0.15)",
    color: "#fff",
    borderRadius: 20,
    padding: "5px 14px",
    fontSize: 12,
    fontWeight: 500,
  },
  content: { padding: "16px 24px", maxWidth: 760, margin: "0 auto", width: "100%", boxSizing: "border-box" },
  count: { fontSize: 13, color: "#999", margin: "0 0 12px" },
  loadingGrid: { display: "flex", flexDirection: "column", gap: 12, marginTop: 8 },
  skeleton: {
    height: 140,
    background: "linear-gradient(90deg, #ececec 25%, #f5f5f5 50%, #ececec 75%)",
    borderRadius: 12,
    animation: "pulse 1.5s infinite",
  },
  errorBox: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    background: "#fdf0f0",
    border: "1px solid #fcc",
    borderRadius: 10,
    padding: "14px 16px",
    color: "#c0392b",
    fontSize: 14,
    marginTop: 16,
  },
  errorIcon: { fontSize: 18 },
  empty: { textAlign: "center", marginTop: 60, padding: "0 20px" },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  emptyText: { fontSize: 17, fontWeight: 700, color: "#aaa", margin: "0 0 6px" },
  emptyHint: { fontSize: 13, color: "#ccc" },
};
