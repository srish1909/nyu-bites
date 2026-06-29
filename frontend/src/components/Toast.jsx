import React, { useEffect, useState } from "react";

export function useToast() {
  const [toast, setToast] = useState(null);
  const show = (msg, type = "info") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };
  return { toast, show };
}

export default function Toast({ toast }) {
  if (!toast) return null;
  const bg = toast.type === "error" ? "#c0392b" : toast.type === "success" ? "#27ae60" : "#333";
  return (
    <div style={{ ...s.toast, background: bg }}>
      {toast.msg}
    </div>
  );
}

const s = {
  toast: {
    position: "fixed",
    bottom: 28,
    left: "50%",
    transform: "translateX(-50%)",
    color: "#fff",
    padding: "12px 24px",
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 500,
    zIndex: 9999,
    boxShadow: "0 4px 16px rgba(0,0,0,0.2)",
    whiteSpace: "nowrap",
  },
};
