import React from "react";
import { Download, Bot, Moon, Sun, BarChart3 } from "lucide-react";

interface HeaderProps {
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onOpenAIModal: () => void;
  exportUrl: string;
}

export const Header: React.FC<HeaderProps> = ({
  theme,
  onToggleTheme,
  onOpenAIModal,
  exportUrl,
}) => {
  return (
    <header className="glass-card" style={{ padding: "16px 24px", marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        {/* Brand & Subtitle */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 12px rgba(99, 102, 241, 0.4)",
            }}
          >
            <BarChart3 size={24} color="white" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h1 style={{ fontSize: "1.35rem", fontWeight: 700 }}>AI BI Analytics Dashboard</h1>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(16, 185, 129, 0.15)", padding: "2px 8px", borderRadius: "12px", fontSize: "0.75rem", color: "#34d399", fontWeight: 600 }}>
                <span className="pulse-dot"></span> Live Pipeline
              </div>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Person 2 — Business KPIs, Predictive Analytics & AI Agent Context Layer
            </p>
          </div>
        </div>

        {/* Controls / Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="btn btn-secondary" onClick={onOpenAIModal} title="Inspect AI Agent context payload">
            <Bot size={18} color="var(--accent-indigo)" />
            AI Context Inspector
          </button>

          <a href={exportUrl} download className="btn btn-primary" style={{ textDecoration: "none" }}>
            <Download size={18} />
            Export CSV
          </a>

          <button
            className="btn btn-secondary"
            onClick={onToggleTheme}
            style={{ width: "40px", height: "40px", padding: 0, justifyContent: "center" }}
            title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
          >
            {theme === "dark" ? <Sun size={20} color="#fbbf24" /> : <Moon size={20} color="#6366f1" />}
          </button>
        </div>
      </div>
    </header>
  );
};
