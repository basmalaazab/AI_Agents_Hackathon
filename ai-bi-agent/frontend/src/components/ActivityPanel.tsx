import React from "react";
import { Activity } from "lucide-react";

/**
 * ActivityPanel – shows recent sync/pipeline events and API activity log.
 *
 * NOTE: A live activity/pipeline log requires a backend endpoint
 * (e.g. GET /api/v1/activity or GET /api/v1/pipeline/runs).
 * This panel currently shows a placeholder explaining that requirement
 * rather than inventing fake activity data.
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
          Activity Log Not Yet Available
        </h3>
        <p style={{ fontSize: "0.875rem", maxWidth: "420px", margin: "0 auto", lineHeight: 1.6 }}>
          A pipeline and sync activity log requires the backend to expose an activity feed endpoint.
          Once available at <code style={{ fontSize: "0.8rem" }}>/api/v1/activity</code>, this section
          will show: sync runs, row counts, errors, and timestamps per source.
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
              background: "rgba(244, 63, 94, 0.08)",
              border: "1px solid rgba(244, 63, 94, 0.2)",
              fontSize: "0.8rem",
              color: "var(--accent-rose)",
            }}
            role="status"
          >
            <span aria-hidden="true">●</span>
            Backend is currently unreachable
          </div>
        )}
      </div>
    </section>
  );
};
