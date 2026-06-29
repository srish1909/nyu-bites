import React, { useState, useEffect } from "react";
import Nav from "./components/Nav";
import Toast, { useToast } from "./components/Toast";
import AgentChat from "./components/AgentChat";
import Browse from "./pages/Browse";
import Saved from "./pages/Saved";
import Login from "./pages/Login";
import { getMe, logout as apiLogout } from "./api/auth";

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("browse");
  const [authChecked, setAuthChecked] = useState(false);
  const { toast, show } = useToast();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setAuthChecked(true);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      })
      .finally(() => setAuthChecked(true));
  }, []);

  async function handleLogout() {
    const refresh = localStorage.getItem("refresh_token");
    try {
      if (refresh) await apiLogout(refresh);
    } catch {}
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    show("Signed out", "info");
  }

  function handleLogin() {
    getMe()
      .then((u) => {
        setUser(u);
        setView("browse");
      })
      .catch(() => show("Could not load profile", "error"));
  }

  if (!authChecked) {
    return (
      <div style={s.splash}>
        <div style={s.splashLogo}>🍕</div>
        <div style={s.splashText}>NYU Bites</div>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <Login onLogin={handleLogin} />
        <Toast toast={toast} />
      </>
    );
  }

  return (
    <div style={s.shell}>
      <Nav view={view} setView={setView} user={user} onLogout={handleLogout} />
      <main style={s.main}>
        {view === "browse" && <Browse />}
        {view === "saved" && <Saved />}
        {view === "agent" && <AgentChat />}
      </main>
      <Toast toast={toast} />
    </div>
  );
}

const s = {
  shell: { minHeight: "100vh", background: "#f7f7f7", fontFamily: "system-ui, -apple-system, sans-serif" },
  main: { flex: 1 },
  splash: {
    minHeight: "100vh",
    background: "#57068c",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  splashLogo: { fontSize: 52 },
  splashText: { color: "#fff", fontSize: 24, fontWeight: 700 },
};
