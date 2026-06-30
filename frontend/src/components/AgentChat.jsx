import React, { useState, useRef, useEffect } from "react";
import { askAgent } from "../api/restaurants";

const SUGGESTIONS = [
  "Find me cheap pizza near campus",
  "What offers free items for NYU students?",
  "Best coffee shops open late?",
  "Where can I get the biggest discount?",
];

export default function AgentChat({ userLocation, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm NYU Bites AI 👋\nAsk me anything about student deals near campus.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function send(text) {
    const q = (text || input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const answer = await askAgent(q, userLocation?.lat ?? null, userLocation?.lng ?? null);
      setMessages(m => [...m, {
        role: "assistant",
        text: answer || "I couldn't find anything for that. Try rephrasing!",
      }]);
    } catch (err) {
      setMessages(m => [...m, {
        role: "assistant",
        text: err?.response?.status === 401
          ? "Please log in again to use the AI."
          : "Something went wrong. Please try again.",
      }]);
    } finally {
      setLoading(false);
    }
  }

  const hasUserMsg = messages.some(m => m.role === "user");

  return (
    <div style={s.panel}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span style={s.headerIcon}>✦</span>
          <div>
            <div style={s.headerTitle}>NYU Bites AI</div>
            <div style={s.headerSub}>Powered by Groq · llama-3.3-70b</div>
          </div>
        </div>
        <button style={s.closeBtn} onClick={onClose} title="Close">✕</button>
      </div>

      {/* Suggestion chips */}
      {!hasUserMsg && (
        <div style={s.suggestions}>
          {SUGGESTIONS.map(s_ => (
            <button key={s_} style={s.chip} onClick={() => send(s_)}>
              {s_}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={s.messages}>
        {messages.map((m, i) => (
          <div key={i} style={m.role === "user" ? s.userRow : s.aiRow}>
            {m.role === "assistant" && <div style={s.aiAvatar}>AI</div>}
            <div style={m.role === "user" ? s.userBubble : s.aiBubble}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={s.aiRow}>
            <div style={s.aiAvatar}>AI</div>
            <div style={s.aiBubble}>
              <span style={s.dot} /><span style={s.dot} /><span style={s.dot} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={s.inputRow}>
        <input
          ref={inputRef}
          style={s.input}
          placeholder="Ask about deals, hours, cuisine…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          disabled={loading}
        />
        <button
          style={{ ...s.sendBtn, opacity: (!input.trim() || loading) ? 0.45 : 1 }}
          onClick={() => send()}
          disabled={!input.trim() || loading}
        >
          ↑
        </button>
      </div>
    </div>
  );
}

const PURPLE = "#57068c";

const s = {
  panel: {
    display: "flex",
    flexDirection: "column",
    width: 360,
    height: 520,
    background: "#fff",
    borderRadius: 20,
    boxShadow: "0 20px 60px rgba(0,0,0,0.2), 0 4px 16px rgba(87,6,140,0.15)",
    overflow: "hidden",
    fontFamily: "system-ui, -apple-system, sans-serif",
    border: "1px solid rgba(87,6,140,0.12)",
  },

  /* header */
  header: {
    background: `linear-gradient(135deg, #3d0066, ${PURPLE})`,
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexShrink: 0,
  },
  headerLeft: { display: "flex", alignItems: "center", gap: 10 },
  headerIcon: { fontSize: 22, color: "#fff" },
  headerTitle: { color: "#fff", fontWeight: 700, fontSize: 15 },
  headerSub: { color: "rgba(255,255,255,0.55)", fontSize: 10, marginTop: 1 },
  closeBtn: {
    background: "rgba(255,255,255,0.15)",
    border: "none",
    color: "#fff",
    borderRadius: "50%",
    width: 28,
    height: 28,
    cursor: "pointer",
    fontSize: 13,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "inherit",
  },

  /* suggestions */
  suggestions: {
    padding: "10px 12px 4px",
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
    flexShrink: 0,
    borderBottom: "1px solid #f1f5f9",
  },
  chip: {
    background: "#faf5ff",
    border: "1px solid #e9d5ff",
    borderRadius: 16,
    padding: "5px 10px",
    fontSize: 11,
    color: PURPLE,
    cursor: "pointer",
    fontFamily: "inherit",
    fontWeight: 500,
    lineHeight: 1.3,
    textAlign: "left",
  },

  /* messages */
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "12px 12px 4px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  aiRow: { display: "flex", alignItems: "flex-end", gap: 6 },
  userRow: { display: "flex", justifyContent: "flex-end" },
  aiAvatar: {
    background: PURPLE,
    color: "#fff",
    borderRadius: "50%",
    width: 26,
    height: 26,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 9,
    fontWeight: 800,
    flexShrink: 0,
  },
  aiBubble: {
    background: "#f4f4f8",
    borderRadius: "16px 16px 16px 4px",
    padding: "9px 12px",
    fontSize: 13,
    lineHeight: 1.5,
    color: "#1e293b",
    whiteSpace: "pre-wrap",
    maxWidth: 260,
    display: "flex",
    gap: 3,
    alignItems: "center",
  },
  userBubble: {
    background: PURPLE,
    color: "#fff",
    borderRadius: "16px 16px 4px 16px",
    padding: "9px 12px",
    fontSize: 13,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
    maxWidth: 260,
  },
  dot: {
    display: "inline-block",
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "#94a3b8",
    animation: "bounce 1.2s infinite",
  },

  /* input */
  inputRow: {
    display: "flex",
    gap: 8,
    padding: "10px 12px",
    borderTop: "1px solid #f1f5f9",
    flexShrink: 0,
  },
  input: {
    flex: 1,
    padding: "9px 14px",
    border: "1.5px solid #e2e8f0",
    borderRadius: 20,
    fontSize: 13,
    outline: "none",
    fontFamily: "inherit",
    color: "#1e293b",
  },
  sendBtn: {
    background: PURPLE,
    color: "#fff",
    border: "none",
    borderRadius: "50%",
    width: 36,
    height: 36,
    cursor: "pointer",
    fontSize: 18,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    transition: "opacity 0.15s",
  },
};
