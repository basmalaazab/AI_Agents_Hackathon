import React, { useState } from "react";
import { X, Copy, Check, Bot, Sparkles } from "lucide-react";

interface AIContextModalProps {
  isOpen: boolean;
  onClose: () => void;
  aiData: any;
}

export const AIContextModal: React.FC<AIContextModalProps> = ({
  isOpen,
  onClose,
  aiData,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(aiData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <div
        className="glass-card animate-fade-in"
        style={{
          width: "100%",
          maxWidth: "800px",
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "20px",
          border: "1px solid var(--accent-indigo)",
        }}
      >
        {/* Modal Header */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--card-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={20} color="#fff" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                Person 3 — AI Agent Structured Analytics Payload <Sparkles size={16} color="#fbbf24" />
              </h3>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                This structured context is exposed via GET /api/v1/analytics/ai-context for Person 3's LLM reasoning
              </p>
            </div>
          </div>

          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          <div style={{ marginBottom: "16px", padding: "12px 16px", background: "rgba(99, 102, 241, 0.1)", borderRadius: "10px", border: "1px solid rgba(99, 102, 241, 0.2)", fontSize: "0.85rem", color: "#cbd5e1" }}>
            💡 <strong>How Person 3's AI Agent will use this data:</strong>
            <br />
            When a user asks questions like <em>"Why did revenue drop this month?"</em> or <em>"Which product should we focus on next?"</em>, the AI Agent fetches this exact JSON payload directly to perform metric reasoning, anomaly diagnosis, and recommendation generation without scraping UI.
          </div>

          <div style={{ position: "relative" }}>
            <button
              onClick={handleCopy}
              className="btn btn-secondary"
              style={{ position: "absolute", top: "12px", right: "12px", fontSize: "0.75rem", padding: "4px 10px", zIndex: 10 }}
            >
              {copied ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
              {copied ? "Copied!" : "Copy JSON"}
            </button>

            <pre
              style={{
                background: "#090d16",
                padding: "16px",
                borderRadius: "12px",
                fontSize: "0.8rem",
                color: "#34d399",
                fontFamily: "monospace",
                overflowX: "auto",
                maxHeight: "420px",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              {JSON.stringify(aiData, null, 2)}
            </pre>
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--card-border)", display: "flex", justifyContent: "flex-end" }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
