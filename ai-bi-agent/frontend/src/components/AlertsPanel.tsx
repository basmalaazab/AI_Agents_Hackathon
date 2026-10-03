import React from "react";
import { AlertTriangle, AlertCircle, CheckCircle2, Info } from "lucide-react";
import type { BusinessAlert } from "../types/analytics";



interface AlertsPanelProps {
  alerts: BusinessAlert[];
  isLoading: boolean;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts, isLoading }) => {
  if (isLoading || !alerts) {
    return null;
  }

  if (alerts.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "16px 24px", marginBottom: "24px", display: "flex", alignItems: "center", gap: "12px" }}>
        <CheckCircle2 size={20} color="var(--accent-emerald)" />
        <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          All operational KPIs and order performance metrics are within normal baseline ranges.
        </span>
      </div>
    );
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "danger":
        return <AlertTriangle size={20} color="var(--accent-rose)" />;
      case "warning":
        return <AlertCircle size={20} color="var(--accent-amber)" />;
      case "success":
        return <CheckCircle2 size={20} color="var(--accent-emerald)" />;
      default:
        return <Info size={20} color="var(--accent-indigo)" />;
    }
  };

  const getSeverityBorder = (severity: string) => {
    switch (severity) {
      case "danger":
        return "1px solid rgba(244, 63, 94, 0.4)";
      case "warning":
        return "1px solid rgba(245, 158, 11, 0.4)";
      case "success":
        return "1px solid rgba(16, 185, 129, 0.4)";
      default:
        return "1px solid rgba(99, 102, 241, 0.4)";
    }
  };

  return (
    <div className="glass-card" style={{ padding: "20px 24px", marginBottom: "24px" }}>
      <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
        <AlertTriangle size={18} color="var(--accent-amber)" /> Business Intelligence Alerts & Signal Detector
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
        {alerts.map((a) => (
          <div
            key={a.id}
            style={{
              padding: "14px 16px",
              borderRadius: "12px",
              background: "var(--card-subtle-bg)",
              border: getSeverityBorder(a.severity),
              display: "flex",
              alignItems: "flex-start",
              gap: "12px",
            }}
          >
            <div style={{ marginTop: "2px" }}>{getSeverityIcon(a.severity)}</div>
            <div>
              <h4 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: "4px" }}>{a.title}</h4>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>{a.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
