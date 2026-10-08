import React from "react";
import { Download, Bot, Moon, Sun, BarChart3, LayoutDashboard, Brain, Database, Activity, Users } from "lucide-react";
import type { AuthUser } from "../services/auth";

export type NavSection = "overview" | "analyst" | "sources" | "team" | "activity";

interface HeaderProps {
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onOpenAIModal: () => void;
  onExport: () => void;
  user: AuthUser;
  onLogout: () => void;
  activeSection: NavSection;
  onSectionChange: (section: NavSection) => void;
}

const NAV_TABS: { id: NavSection; label: string; Icon: React.ComponentType<{ size?: number }> }[] = [
  { id: "overview",  label: "Overview",     Icon: LayoutDashboard },
  { id: "analyst",   label: "AI Analyst",   Icon: Brain },
  { id: "sources",   label: "Data Sources", Icon: Database },
  { id: "team",      label: "Team",         Icon: Users },
  { id: "activity",  label: "Activity",     Icon: Activity },
];

export const Header: React.FC<HeaderProps> = ({
  theme,
  onToggleTheme,
  onOpenAIModal,
  onExport,
  user,
  onLogout,
  activeSection,
  onSectionChange,
}) => {
  return (
    <header
      className="glass-card"
      style={{ padding: "16px 24px", marginBottom: "24px" }}
      role="banner"
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            aria-hidden="true"
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #246b4d 0%, #24845a 100%)",
              boxShadow: "0 2px 8px rgba(36, 107, 77, 0.25)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <BarChart3 size={22} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: "1.15rem", fontWeight: 700, lineHeight: 1.2, color: "var(--text-primary)" }}>
              Clearview BI
            </h1>
            <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Business insights from your data
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="app-header-controls" style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <button
            className="btn btn-primary"
            onClick={onOpenAIModal}
            aria-label="Open AI Business Analyst"
            title="Open AI Business Analyst"
            style={{
              background: "linear-gradient(135deg, #246b4d 0%, #24845a 100%)",
              boxShadow: "0 2px 6px rgba(36, 107, 77, 0.2)",
              color: "#ffffff",
              fontSize: "0.85rem",
              padding: "9px 16px",
              border: "none",
            }}
          >
            <Bot size={17} />
            <span>Ask AI Analyst</span>
          </button>

          <button
            onClick={onExport}
            className="btn btn-secondary"
            style={{ textDecoration: "none", fontSize: "0.85rem", padding: "9px 14px" }}
            aria-label="Export data as CSV"
            title="Export data as CSV"
          >
            <Download size={16} />
            <span>Export CSV</span>
          </button>

          <span style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{user.business_name}</span>
          <button className="btn btn-secondary" onClick={onLogout} style={{ fontSize: "0.82rem", padding: "9px 12px" }}>Sign out</button>

          <button
            className="btn btn-secondary"
            onClick={onToggleTheme}
            style={{ width: "38px", height: "38px", padding: 0, justifyContent: "center", flexShrink: 0 }}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
          >
            {theme === "dark" ? <Sun size={18} color="var(--accent-amber)" /> : <Moon size={18} color="var(--accent-indigo)" />}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav
        aria-label="Workspace sections"
        style={{ marginTop: "16px" }}
      >
        <div className="app-nav" role="tablist">
          {NAV_TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              role="tab"
              aria-selected={activeSection === id}
              aria-label={label}
              title={label}
              className={`nav-tab${activeSection === id ? " active" : ""}`}
              onClick={() => onSectionChange(id)}
            >
              <Icon size={16} />
              <span className="nav-label">{label}</span>
            </button>
          ))}
        </div>
      </nav>
    </header>
  );
};
