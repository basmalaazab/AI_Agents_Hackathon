import React from "react";
import { AlertTriangle, AlertCircle, CheckCircle2, Info, WifiOff } from "lucide-react";
import type { BusinessAlert } from "../types/analytics";

interface AlertsPanelProps {
  alerts: BusinessAlert[];
  isLoading: boolean;
  apiOffline?: boolean;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts, isLoading, apiOffline }) => {
  // While loading, render nothing (KPICards shows its own skeleton)
  if (isLoading) return null;

  // If the API is offline we should not show "all KPIs normal"
  if (apiOffline) {
    return (
      <div
        className="glass-card"
        style={{
          padding: "14px 20px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          borderColor: "var(--accent-border-danger)",
        }}
        role="status"
        aria-live="polite"
      >
        <WifiOff size={18} color="var(--accent-rose)" aria-hidden="true" />
        <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          The analytics service is unavailable, so alerts could not be loaded.
        </span>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div
        className="glass-card"
        style={{ padding: "14px 20px", marginBottom: "24px", display: "flex", alignItems: "center", gap: "10px" }}
        role="status"
        aria-live="polite"
      >
        <CheckCircle2 size={18} color="var(--accent-emerald)" aria-hidden="true" />
        <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          No alerts were generated for the selected period.
        </span>
      </div>
    );
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "danger":
        return <AlertTriangle size={18} color="var(--accent-rose)" aria-hidden="true" />;
      case "warning":
        return <AlertCircle size={18} color="var(--accent-amber)" aria-hidden="true" />;
      case "success":
        return <CheckCircle2 size={18} color="var(--accent-emerald)" aria-hidden="true" />;
      default:
        return <Info size={18} color="var(--accent-indigo)" aria-hidden="true" />;
    }
  };

  const getSeverityBorder = (severity: string) => {
    switch (severity) {
      case "danger":  return "1px solid var(--accent-border-danger)";
      case "warning": return "1px solid var(--accent-border-warning)";
      case "success": return "1px solid var(--accent-border-success)";
      default:        return "1px solid var(--accent-border-info)";
    }
  };

  return (
    <section
      className="glass-card"
      style={{ padding: "18px 22px", marginBottom: "24px" }}
      aria-labelledby="alerts-heading"
    >
      <h2
        id="alerts-heading"
        style={{
          fontSize: "0.875rem",
          fontWeight: 700,
          marginBottom: "12px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          color: "var(--text-primary)",
        }}
      >
        <AlertTriangle size={16} color="var(--accent-amber)" aria-hidden="true" />
        Alerts
        <span
          style={{
            marginLeft: "auto",
            fontSize: "0.72rem",
            padding: "2px 8px",
            borderRadius: "10px",
            background: "var(--badge-red-bg)",
            color: "var(--badge-red-text)",
            fontWeight: 600,
          }}
        >
          {alerts.length} active
        </span>
      </h2>

      <div
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}
        role="list"
        aria-label="Business alerts"
      >
        {alerts.map((a) => (
          <div
            key={a.id}
            role="listitem"
            style={{
              padding: "12px 14px",
              borderRadius: "10px",
              background: "var(--card-subtle-bg)",
              border: getSeverityBorder(a.severity),
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
            }}
          >
            <div style={{ marginTop: "1px", flexShrink: 0 }}>{getSeverityIcon(a.severity)}</div>
            <div style={{ minWidth: 0 }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 700, marginBottom: "3px" }}>{a.title}</h3>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.45, margin: 0 }}>
                {a.message}
              </p>
              {(a.change_pct !== undefined || a.value !== undefined) && (
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {a.metric && <>Metric: <strong>{a.metric.replaceAll("_", " ")}</strong></>}
                  {a.change_pct !== undefined && <> · Change: <strong>{a.change_pct > 0 ? "+" : ""}{a.change_pct}%</strong></>}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
