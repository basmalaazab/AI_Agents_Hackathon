import React from "react";
import { Download, Bot, Moon, Sun, LayoutDashboard, Brain, Database, Activity, Users, Printer, ChartNoAxesCombined } from "lucide-react";
import type { AuthUser } from "../services/auth";

export type NavSection = "overview" | "performance" | "analyst" | "sources" | "team" | "activity";

interface HeaderProps {
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onOpenAIModal: () => void;
  onExport: () => void;
  onPrintReport: () => void;
  user: AuthUser;
  onLogout: () => void;
  activeSection: NavSection;
  onSectionChange: (section: NavSection) => void;
}

const NAV_TABS: { id: NavSection; label: string; Icon: React.ComponentType<{ size?: number }> }[] = [
  { id: "overview",  label: "Overview",     Icon: LayoutDashboard },
  { id: "performance", label: "Performance", Icon: ChartNoAxesCombined },
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
  onPrintReport,
  user,
  onLogout,
  activeSection,
  onSectionChange,
}) => {
  return (
    <header
      className="glass-card app-header"
      style={{ padding: "18px 22px", marginBottom: "24px" }}
      role="banner"
    >
      <div className="app-header-top">
        {/* Brand */}
        <a className="brand-lockup" href="#overview" onClick={(event) => { event.preventDefault(); onSectionChange("overview"); }} aria-label="Clearview BI home">
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <div className="brand-copy">
            <h1>
              Clearview BI
            </h1>
            <p>
              Your business, in clear view
            </p>
          </div>
        </a>

        {/* Controls */}
        <div className="app-header-controls">
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
            aria-label="Export executive report as Excel workbook"
            title="Download executive Excel workbook"
          >
            <Download size={16} />
            <span>Export Excel</span>
          </button>

          <button
            onClick={onPrintReport}
            className="btn btn-secondary"
            style={{ textDecoration: "none", fontSize: "0.85rem", padding: "9px 14px" }}
            aria-label="Print or Save Executive PDF Report"
            title="Print or Save Executive PDF Report"
          >
            <Printer size={16} />
            <span>Print / PDF</span>
          </button>

          <span className="workspace-chip" title={`Signed in to ${user.business_name}`}><span>Workspace</span><strong>{user.business_name}</strong></span>
          <button className="btn btn-quiet" onClick={onLogout}>Sign out</button>

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
        className="app-header-nav"
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
              aria-current={activeSection === id ? "page" : undefined}
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
