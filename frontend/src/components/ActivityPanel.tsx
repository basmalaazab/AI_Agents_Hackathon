import React from "react";
import { Activity } from "lucide-react";

/**
 * Activity history is not available yet; pipeline totals are shown under Data Sources.
 */

export const ActivityPanel: React.FC<{ apiOffline: boolean }> = ({ apiOffline }) => {
  return (
    <section aria-labelledby="activity-title">
      <div
        style={{
          padding: "48px 24px",
          textAlign: "center",
          color: "var(--text-secondary)",
        }}
        className="glass-card"
      >
        <Activity size={36} color="var(--text-muted)" style={{ margin: "0 auto 14px" }} aria-hidden="true" />
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
          Activity history isn’t available yet
        </h3>
        <p style={{ fontSize: "0.875rem", maxWidth: "420px", margin: "0 auto", lineHeight: 1.6 }}>
          This section will show recent imports, sync results, and errors once activity history is added.
          For the current pipeline totals, open <strong>Data Sources</strong>.
        </p>
        {apiOffline && (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              marginTop: "16px",
              padding: "6px 14px",
              borderRadius: "20px",
              background: "var(--badge-red-bg)",
              border: "1px solid var(--accent-border-danger)",
              fontSize: "0.8rem",
              color: "var(--accent-rose)",
            }}
            role="status"
          >
            <span aria-hidden="true">●</span>
            The backend is currently unreachable.
          </div>
        )}
      </div>
    </section>
  );
};
