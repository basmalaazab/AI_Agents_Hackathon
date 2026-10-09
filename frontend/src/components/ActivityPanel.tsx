import React, { useEffect, useState } from "react";
import { Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw, Filter, Database, Clock } from "lucide-react";
import { fetchPipelineRuns, fetchDataSources, fetchAuditEvents, type PipelineRunInfo, type DataSourceInfo, type AuditEventInfo } from "../services/api";

interface ActivityPanelProps {
  apiOffline: boolean;
}

export const ActivityPanel: React.FC<ActivityPanelProps> = ({ apiOffline }) => {
  const [runs, setRuns] = useState<PipelineRunInfo[]>([]);
  const [sources, setSources] = useState<Record<string, DataSourceInfo>>({});
  const [accountEvents, setAccountEvents] = useState<AuditEventInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<"all" | "success" | "partial" | "failed">("all");

  const loadData = async () => {
    setLoading(true);
    try {
      const [runsData, sourcesData, auditData] = await Promise.all([
        fetchPipelineRuns(50),
        fetchDataSources().catch(() => []),
        fetchAuditEvents(50).catch(() => []),
      ]);
      setRuns(runsData);
      setAccountEvents(auditData);
      const sourceMap: Record<string, DataSourceInfo> = {};
      sourcesData.forEach((s) => {
        sourceMap[s.id] = s;
      });
      setSources(sourceMap);
    } catch (err) {
      console.error("Failed to fetch activity runs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!apiOffline) {
      loadData();
    }
  }, [apiOffline]);

  const filteredRuns = runs.filter((r) => {
    if (filterStatus === "all") return true;
    return r.status.toLowerCase() === filterStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "success":
      case "completed":
        return (
          <span className="badge badge-emerald" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <CheckCircle size={12} /> Completed
          </span>
        );
      case "partial":
        return (
          <span className="badge badge-amber" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <AlertTriangle size={12} /> Partial
          </span>
        );
      case "failed":
        return (
          <span className="badge badge-rose" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <XCircle size={12} /> Failed
          </span>
        );
      default:
        return <span className="badge badge-indigo">{status}</span>;
    }
  };

  return (
    <section aria-labelledby="activity-title" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header and filters */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h2 id="activity-title" style={{ fontSize: "1.25rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <Activity size={20} color="var(--accent-indigo)" />
            Activity & Ingestion Audit Log
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Real-time chronological log of data syncs, CSV imports, pipeline runs, and quality alerts.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "var(--bg-secondary)", borderRadius: "8px", padding: "4px 8px" }}>
            <Filter size={14} color="var(--text-muted)" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              style={{ background: "transparent", border: "none", color: "var(--text-primary)", fontSize: "0.85rem", cursor: "pointer", outline: "none" }}
            >
              <option value="all">All Events ({runs.length})</option>
              <option value="success">Completed</option>
              <option value="partial">Partial</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="btn btn-secondary"
            style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "0.85rem", padding: "6px 14px" }}
            title="Refresh Activity"
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {apiOffline && (
        <div className="glass-card" style={{ padding: "12px 18px", borderLeft: "4px solid var(--accent-rose)", color: "var(--accent-rose)", fontSize: "0.875rem" }}>
          ⚠️ Backend is currently unreachable. Activity records cannot be refreshed.
        </div>
      )}

      <section className="glass-card audit-account-card" aria-labelledby="account-activity-title">
        <div className="audit-account-heading"><div><h3 id="account-activity-title">Workspace activity</h3><p>Recent sign-ins and company account events.</p></div><span>{accountEvents.length} events</span></div>
        {accountEvents.length === 0 ? <p className="rfm-empty">No account activity recorded yet.</p> : <ul className="audit-account-list">
          {accountEvents.map((event) => <li key={event.id}><span className="audit-account-dot" /><div><strong>{event.summary}</strong><small>{event.user} · {new Date(event.created_at).toLocaleString()}</small></div></li>)}
        </ul>}
      </section>

      {loading && runs.length === 0 ? (
        <div className="glass-card" style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
          <RefreshCw size={24} className="spin" style={{ margin: "0 auto 10px" }} />
          Loading audit log events...
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="glass-card" style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-secondary)" }}>
          <Database size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
          <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
            No activity found
          </h3>
          <p style={{ fontSize: "0.875rem", maxWidth: "400px", margin: "0 auto" }}>
            {filterStatus !== "all" ? `No runs found matching status "${filterStatus}".` : "No pipeline runs have been executed yet in this workspace."}
          </p>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: "0", overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(255, 255, 255, 0.03)", borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.75rem", textTransform: "uppercase" }}>
                  <th style={{ padding: "12px 16px" }}>Timestamp</th>
                  <th style={{ padding: "12px 16px" }}>Data Source</th>
                  <th style={{ padding: "12px 16px" }}>Type</th>
                  <th style={{ padding: "12px 16px" }}>Status</th>
                  <th style={{ padding: "12px 16px" }}>Records Ingested</th>
                  <th style={{ padding: "12px 16px" }}>Duplicates</th>
                  <th style={{ padding: "12px 16px" }}>Invalid</th>
                  <th style={{ padding: "12px 16px" }}>Trigger</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((run) => {
                  const src = sources[run.data_source_id];
                  const sourceName = src ? (src.display_name || src.name) : "CSV / Pipeline";
                  const sourceType = src ? src.source_type : (run.record_type || "batch");
                  const dateStr = run.started_at ? new Date(run.started_at).toLocaleString() : "Unknown";

                  return (
                    <tr key={run.id} style={{ borderBottom: "1px solid var(--border-color)" }}>
                      <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <Clock size={13} color="var(--text-muted)" />
                          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{dateStr}</span>
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px", fontWeight: 600 }}>
                        {sourceName}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className="badge badge-slate" style={{ textTransform: "uppercase", fontSize: "0.7rem" }}>
                          {sourceType}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        {getStatusBadge(run.status)}
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--accent-emerald)", fontWeight: 600 }}>
                        +{run.records_inserted}
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--text-muted)" }}>
                        {run.records_duplicate}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        {run.records_invalid > 0 ? (
                          <span style={{ color: "var(--accent-rose)", fontWeight: 600 }}>
                            {run.records_invalid} error{run.records_invalid > 1 ? "s" : ""}
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>0</span>
                        )}
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                        {run.error_message ? (
                          <span title={run.error_message} style={{ color: "var(--accent-rose)", cursor: "help" }}>
                            ⚠️ {run.error_message.slice(0, 30)}...
                          </span>
                        ) : (
                          "Manual / API"
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
};
export default ActivityPanel;
