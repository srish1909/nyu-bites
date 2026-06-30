import React from "react";

export default function Nav({ view, setView, user, onLogout }) {
  return (
    <nav style={s.nav}>
      <div style={s.brand}>
        <span style={s.logo}>🍕</span>
        <span style={s.brandName}>NYU Bites</span>
      </div>

      <div style={s.links}>
        {[
          { id: "browse", label: "Browse" },
          { id: "saved", label: "Saved" },
        ].map(({ id, label }) => (
          <button
            key={id}
            style={{ ...s.link, ...(view === id ? s.linkActive : {}) }}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={s.right}>
        {user && (
          <span style={s.userLabel}>
            {user.display_name || user.nyu_email.split("@")[0]}
          </span>
        )}
        <button style={s.logoutBtn} onClick={onLogout}>
          Sign out
        </button>
      </div>
    </nav>
  );
}

const s = {
  nav: {
    position: "sticky",
    top: 0,
    zIndex: 100,
    background: "#57068c",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: 56,
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  },
  brand: { display: "flex", alignItems: "center", gap: 8 },
  logo: { fontSize: 22 },
  brandName: { color: "#fff", fontWeight: 700, fontSize: 18, letterSpacing: "-0.3px" },
  links: { display: "flex", gap: 4 },
  link: {
    background: "none",
    border: "none",
    color: "rgba(255,255,255,0.75)",
    cursor: "pointer",
    padding: "6px 16px",
    borderRadius: 20,
    fontSize: 14,
    fontWeight: 500,
    transition: "all 0.15s",
  },
  linkActive: {
    background: "rgba(255,255,255,0.15)",
    color: "#fff",
  },
  right: { display: "flex", alignItems: "center", gap: 12 },
  userLabel: { color: "rgba(255,255,255,0.7)", fontSize: 13 },
  logoutBtn: {
    background: "rgba(255,255,255,0.12)",
    border: "1px solid rgba(255,255,255,0.2)",
    color: "#fff",
    cursor: "pointer",
    padding: "5px 14px",
    borderRadius: 20,
    fontSize: 13,
  },
};
