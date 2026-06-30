import React from "react";

const CUISINES = [
  "All", "Pizza", "Cafe", "Mexican", "Chinese",
  "Middle Eastern", "Italian", "American", "Falafel", "Bagels",
];

const DISCOUNT_TYPES = [
  { value: "", label: "Any Deal" },
  { value: "percentage", label: "% Off" },
  { value: "fixed", label: "$ Off" },
  { value: "free_item", label: "Free Item" },
  { value: "special_menu", label: "Student Menu" },
];

export default function FilterBar({ filters, onChange }) {
  const set = (key, value) => onChange({ ...filters, [key]: value });

  return (
    <div style={s.bar}>
      {/* Search */}
      <input
        style={s.search}
        placeholder="Search restaurants..."
        value={filters.search || ""}
        onChange={(e) => set("search", e.target.value)}
      />

      {/* Cuisine pills */}
      <div style={s.pills}>
        {CUISINES.map((c) => {
          const val = c === "All" ? "" : c;
          const active = (filters.cuisine_type || "") === val;
          return (
            <button
              key={c}
              style={{ ...s.pill, ...(active ? s.pillActive : {}) }}
              onClick={() => set("cuisine_type", val)}
            >
              {c}
            </button>
          );
        })}
      </div>

      {/* Bottom row: discount + open now + verified */}
      <div style={s.row}>
        <select
          style={s.select}
          value={filters.discount_type || ""}
          onChange={(e) => set("discount_type", e.target.value)}
        >
          {DISCOUNT_TYPES.map((d) => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>

        <label style={s.toggle}>
          <input
            type="checkbox"
            checked={!!filters.open_now}
            onChange={(e) => set("open_now", e.target.checked)}
            style={{ accentColor: "#57068c" }}
          />
          <span>Open now</span>
        </label>

        <label style={s.toggle}>
          <input
            type="checkbox"
            checked={!!filters.is_verified}
            onChange={(e) => set("is_verified", e.target.checked)}
            style={{ accentColor: "#57068c" }}
          />
          <span>Verified only</span>
        </label>
      </div>
    </div>
  );
}

const s = {
  bar: {
    background: "#fff",
    borderBottom: "1px solid #eee",
    padding: "12px 24px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  search: {
    width: "100%",
    padding: "9px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "inherit",
  },
  pills: {
    display: "flex",
    gap: 6,
    flexWrap: "wrap",
  },
  pill: {
    background: "#f5f5f5",
    border: "none",
    borderRadius: 20,
    padding: "5px 13px",
    fontSize: 13,
    cursor: "pointer",
    color: "#555",
    fontFamily: "inherit",
  },
  pillActive: {
    background: "#57068c",
    color: "#fff",
  },
  row: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    flexWrap: "wrap",
  },
  select: {
    padding: "6px 10px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 13,
    outline: "none",
    fontFamily: "inherit",
    cursor: "pointer",
  },
  toggle: {
    display: "flex",
    alignItems: "center",
    gap: 5,
    fontSize: 13,
    color: "#555",
    cursor: "pointer",
    userSelect: "none",
  },
};
