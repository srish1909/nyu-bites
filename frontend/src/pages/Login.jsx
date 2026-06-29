import React, { useState } from "react";
import { login, register } from "../api/auth";

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ nyu_email: "", password: "", display_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setError("");

    if (!form.nyu_email.endsWith("@nyu.edu")) {
      setError("You must use an @nyu.edu email address.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "register") {
        const user = await register(form.nyu_email, form.password, form.display_name);
        if (user.is_verified) {
          // Dev mode: auto-verified — just log straight in
          const data = await login(form.nyu_email, form.password);
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          onLogin();
        } else {
          setRegistered(true); // production: show "check your email"
        }
      } else {
        const data = await login(form.nyu_email, form.password);
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        onLogin();
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Something went wrong.";
      setError(Array.isArray(msg) ? msg[0]?.msg || "Invalid request." : msg);
    } finally {
      setLoading(false);
    }
  }

  if (registered) {
    return (
      <div style={s.outer}>
        <div style={s.card}>
          <div style={s.logo}>🍕</div>
          <h2 style={s.brand}>NYU Bites</h2>
          <div style={s.successBox}>
            <p style={s.successTitle}>Check your email!</p>
            <p style={s.successText}>
              We sent a verification link to <strong>{form.nyu_email}</strong>.
              Click it to activate your account, then sign in.
            </p>
            <button style={s.switchBtn} onClick={() => { setMode("login"); setRegistered(false); }}>
              Back to sign in
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={s.outer}>
      <div style={s.card}>
        <div style={s.logo}>🍕</div>
        <h2 style={s.brand}>NYU Bites</h2>
        <p style={s.tagline}>Student discounts, all in one place</p>

        <div style={s.tabs}>
          {["login", "register"].map((m) => (
            <button
              key={m}
              style={{ ...s.tab, ...(mode === m ? s.tabActive : {}) }}
              onClick={() => { setMode(m); setError(""); }}
            >
              {m === "login" ? "Sign In" : "Sign Up"}
            </button>
          ))}
        </div>

        <form onSubmit={submit} style={s.form}>
          {mode === "register" && (
            <input
              style={s.input}
              placeholder="Display name (optional)"
              value={form.display_name}
              onChange={set("display_name")}
            />
          )}
          <input
            style={s.input}
            type="email"
            placeholder="netid@nyu.edu"
            value={form.nyu_email}
            onChange={set("nyu_email")}
            required
            autoComplete="email"
          />
          <input
            style={s.input}
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={set("password")}
            required
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />

          {error && <div style={s.error}>{error}</div>}

          <button style={s.submit} type="submit" disabled={loading}>
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p style={s.nyuNote}>NYU students only · @nyu.edu required</p>
      </div>
    </div>
  );
}

const s = {
  outer: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #3d0066 0%, #57068c 60%, #7b1fa2 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
  },
  card: {
    background: "#fff",
    borderRadius: 20,
    padding: "36px 32px",
    width: "100%",
    maxWidth: 400,
    boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
    textAlign: "center",
  },
  logo: { fontSize: 44, marginBottom: 4 },
  brand: { margin: "0 0 4px", fontSize: 26, fontWeight: 800, color: "#57068c" },
  tagline: { margin: "0 0 22px", fontSize: 13, color: "#aaa" },
  tabs: {
    display: "flex",
    marginBottom: 22,
    border: "1px solid #eee",
    borderRadius: 10,
    overflow: "hidden",
  },
  tab: {
    flex: 1,
    padding: "9px 0",
    border: "none",
    background: "none",
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
    color: "#999",
    fontFamily: "inherit",
  },
  tabActive: {
    background: "#57068c",
    color: "#fff",
    fontWeight: 700,
  },
  form: { display: "flex", flexDirection: "column", gap: 12 },
  input: {
    padding: "11px 14px",
    border: "1px solid #ddd",
    borderRadius: 10,
    fontSize: 14,
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
    width: "100%",
  },
  error: {
    background: "#fdf0f0",
    border: "1px solid #fcc",
    color: "#c0392b",
    borderRadius: 8,
    padding: "9px 12px",
    fontSize: 13,
    textAlign: "left",
  },
  submit: {
    background: "#57068c",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "12px",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
    fontFamily: "inherit",
    marginTop: 4,
  },
  nyuNote: { fontSize: 12, color: "#ccc", marginTop: 18 },
  successBox: { textAlign: "left" },
  successTitle: { fontWeight: 700, fontSize: 17, color: "#27ae60", marginBottom: 8 },
  successText: { fontSize: 14, color: "#555", lineHeight: 1.5, marginBottom: 16 },
  switchBtn: {
    background: "none",
    border: "1px solid #57068c",
    color: "#57068c",
    borderRadius: 8,
    padding: "8px 18px",
    cursor: "pointer",
    fontSize: 14,
    fontFamily: "inherit",
  },
};
