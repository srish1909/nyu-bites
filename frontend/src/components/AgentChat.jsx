import React, { useState, useRef, useEffect } from "react";
import { askAgent } from "../api/restaurants";

const SUGGESTIONS = [
  "Find me cheap pizza near Washington Square Park",
  "What restaurants offer free items for NYU students?",
  "Best coffee shops open late near campus",
  "Where can I get student discounts on sushi?",
];

export default function AgentChat({ userLocation }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm NYU Bites AI. Ask me anything about student discounts around campus — I'll find the best deals for you.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const q = (text || input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const data = await askAgent(q, userLocation?.lat ?? null, userLocation?.lng ?? null);
      setMessages((m) => [...m, { role: "assistant", text: data.response }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.container}>
      <div style={s.header}>
        <span style={s.headerIcon}>✦</span>
        <div>
          <div style={s.headerTitle}>NYU Bites AI</div>
          <div style={s.headerSub}>Powered by Groq · llama-3.3-70b</div>
        </div>
      </div>

      {/* Suggestion chips — only show before any user message */}
      {messages.filter((m) => m.role === "user").length === 0 && (
        <div style={s.suggestions}>
          {SUGGESTIONS.map((s_) => (
            <button key={s_} style={s.chip} onClick={() => send(s_)}>
              {s_}
            </button>
          ))}
        </div>
      )}

      {/* Message list */}
      <div style={s.messages}>
        {messages.map((m, i) => (
          <div key={i} style={{ ...s.msg, ...(m.role === "user" ? s.userMsg : s.aiMsg) }}>
            {m.role === "assistant" && <span style={s.aiLabel}>AI</span>}
            <div style={s.bubble}>{m.text}</div>
          </div>
        ))}
        {loading && (
          <div style={{ ...s.msg, ...s.aiMsg }}>
            <span style={s.aiLabel}>AI</span>
            <div style={s.bubble}>
              <span style={s.dots}>
                <span>.</span><span>.</span><span>.</span>
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={s.inputRow}>
        <input
          style={s.input}
          placeholder="Ask about deals, hours, cuisine..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={loading}
        />
        <button style={s.sendBtn} onClick={() => send()} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

const s = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "calc(100vh - 56px)",
    maxWidth: 720,
    margin: "0 auto",
    padding: "0 16px 16px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "18px 0 12px",
    borderBottom: "1px solid #eee",
    marginBottom: 12,
  },
  headerIcon: {
    fontSize: 28,
    color: "#57068c",
  },
  headerTitle: { fontWeight: 700, fontSize: 17, color: "#111" },
  headerSub: { fontSize: 11, color: "#aaa", marginTop: 1 },
  suggestions: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 14,
  },
  chip: {
    background: "#faf5ff",
    border: "1px solid #e9d5ff",
    borderRadius: 20,
    padding: "7px 14px",
    fontSize: 13,
    color: "#57068c",
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
    lineHeight: 1.3,
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 12,
    paddingBottom: 8,
  },
  msg: {
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
    maxWidth: "85%",
  },
  aiMsg: { alignSelf: "flex-start" },
  userMsg: { alignSelf: "flex-end", flexDirection: "row-reverse" },
  aiLabel: {
    background: "#57068c",
    color: "#fff",
    borderRadius: "50%",
    width: 28,
    height: 28,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 10,
    fontWeight: 700,
    flexShrink: 0,
  },
  bubble: {
    background: "#f5f5f5",
    borderRadius: 12,
    padding: "10px 14px",
    fontSize: 14,
    lineHeight: 1.55,
    color: "#222",
    whiteSpace: "pre-wrap",
  },
  dots: {
    display: "inline-flex",
    gap: 2,
    animation: "pulse 1s infinite",
  },
  inputRow: {
    display: "flex",
    gap: 8,
    marginTop: 8,
    borderTop: "1px solid #eee",
    paddingTop: 12,
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 24,
    fontSize: 14,
    outline: "none",
    fontFamily: "inherit",
  },
  sendBtn: {
    background: "#57068c",
    color: "#fff",
    border: "none",
    borderRadius: 24,
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
    opacity: 1,
  },
};
