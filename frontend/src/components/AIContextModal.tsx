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
      role="presentation"
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
        role="dialog"
        aria-modal="true"
        aria-label="Analytics context for the AI Analyst"
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
            <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "linear-gradient(135deg, var(--accent-indigo), var(--accent-emerald))", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={20} color="#fff" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                Analytics context for the AI Analyst <Sparkles size={16} color="var(--accent-amber)" />
              </h3>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                A snapshot of the business metrics used to answer your questions
              </p>
            </div>
          </div>

          <button onClick={onClose} aria-label="Close analytics context" style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          <div style={{ marginBottom: "16px", padding: "12px 16px", background: "var(--card-subtle-bg)", borderRadius: "10px", border: "1px solid var(--card-subtle-border)", fontSize: "0.85rem", color: "var(--text-primary)" }}>
            💡 <strong>What this data is for:</strong>
            <br />
            The analyst uses this summary to answer questions about revenue, customers, products, and trends. It cannot see information that has not been imported. If an external AI provider is configured on the backend, this summary and your question are sent to that provider to generate an answer.
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
                background: "var(--code-bg)",
                padding: "16px",
                borderRadius: "12px",
                fontSize: "0.8rem",
                color: "var(--code-text)",
                fontFamily: "monospace",
                overflowX: "auto",
                maxHeight: "420px",
                border: "1px solid var(--card-border)",
              }}
            >
              {JSON.stringify(aiData, null, 2)}
            </pre>
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--card-border)", display: "flex", justifyContent: "flex-end" }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
