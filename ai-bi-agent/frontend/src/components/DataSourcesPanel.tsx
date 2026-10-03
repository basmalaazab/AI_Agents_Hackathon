import React, { useMemo, useState } from "react";
import { Database, Upload, Play, RefreshCw, Plus } from "lucide-react";
import {
  createDataSource,
  fetchPipelineSummary,
  triggerPipeline,
  uploadCsvFile,
  type DataSourceInfo,
  type PipelineSummary,
} from "../services/api";

interface DataSourcesPanelProps {
  sources: DataSourceInfo[];
  summary: PipelineSummary | null;
  onSourcesChanged: () => Promise<void> | void;
}

export const DataSourcesPanel: React.FC<DataSourcesPanelProps> = ({
  sources,
  summary,
  onSourcesChanged,
}) => {
  const [recordType, setRecordType] = useState<"customer" | "product" | "order">("order");
  const [sourceType, setSourceType] = useState<"hubspot" | "stripe">("hubspot");
  const [sourceName, setSourceName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const syncableSources = useMemo(
    () => sources.filter((s) => ["mock_api", "hubspot", "stripe"].includes(s.source_type) && s.is_active),
    [sources]
  );

  const handleRegisterSource = async () => {
    const name = sourceName.trim();
    if (!name) {
      setError("Enter a name for this data source.");
      return;
    }
    setIsRegistering(true);
    setError(null);
    setMessage(null);
    try {
      await createDataSource(name, sourceType);
      setMessage(`Registered ${sourceType} source "${name}". Add its API credential to the backend environment, then sync to verify the connection.`);
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not register data source");
    } finally {
      setIsRegistering(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setIsUploading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await uploadCsvFile(file, recordType, sourceName.trim() || "csv_upload");
      setMessage(
        `Uploaded ${result.records_fetched} ${recordType} rows — inserted ${result.records_inserted}, duplicates ${result.records_duplicate}, invalid ${result.records_invalid}.`
      );
      setFile(null);
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "CSV upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSyncSources = async () => {
    if (syncableSources.length === 0) {
      setError("No active API sources are registered.");
      return;
    }
    setIsSyncing(true);
    setError(null);
    setMessage(null);
    try {
      const totals = { fetched: 0, inserted: 0, duplicate: 0, invalid: 0 };
      const recordTypes: Record<string, Array<"customer" | "product" | "order">> = {
        mock_api: ["customer", "product", "order"],
        hubspot: ["customer", "product"],
        stripe: ["customer", "product", "order"],
      };
      for (const source of syncableSources) {
        for (const type of recordTypes[source.source_type] ?? []) {
          const run = await triggerPipeline(source.id, type);
          if (run.status === "failed") {
            throw new Error(`${source.name}: ${run.error_message ?? "Pipeline failed"}`);
          }
          totals.fetched += run.records_fetched;
          totals.inserted += run.records_inserted;
          totals.duplicate += run.records_duplicate;
          totals.invalid += run.records_invalid;
        }
      }
      setMessage(
        `Synced ${syncableSources.length} API source(s) — fetched ${totals.fetched}, inserted ${totals.inserted}, duplicates ${totals.duplicate}, invalid ${totals.invalid}.`
      );
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Pipeline sync failed");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRefreshSummary = async () => {
    try {
      await fetchPipelineSummary();
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not refresh sources");
    }
  };

  return (
    <div className="glass-card" style={{ padding: "20px 24px", marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", marginBottom: "16px" }}>
        <div>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <Database size={18} color="var(--accent-indigo)" /> Centralized data sources
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Import CSV data or sync connected HubSpot and Stripe accounts into one database.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={handleRefreshSummary} style={{ fontSize: "0.8rem", padding: "8px 12px" }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "10px", marginBottom: "16px" }}>
          {[
            ["Sources", sources.length],
            ["Runs", summary.total_runs],
            ["Customers", summary.total_customers],
            ["Orders", summary.total_orders],
            ["Products", summary.total_products],
            ["Quality issues", summary.total_quality_errors],
          ].map(([label, value]) => (
            <div key={String(label)} style={{ background: "var(--card-subtle-bg)", border: "1px solid var(--card-subtle-border)", borderRadius: "10px", padding: "10px 12px" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{label}</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>
        {sources.length === 0 ? (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>No sources registered yet. Upload a CSV to create one.</span>
        ) : (
          sources.map((s) => (
            <span key={s.id} className="badge badge-positive">
              {s.name} · {s.source_type}
            </span>
          ))
        )}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
        <select className="select-input" value={recordType} onChange={(e) => setRecordType(e.target.value as "customer" | "product" | "order")}>
          <option value="customer">Customers (CRM)</option>
          <option value="order">Orders (Sales / payments)</option>
          <option value="product">Products (Catalog)</option>
        </select>
        <input
          className="select-input"
          value={sourceName}
          onChange={(e) => setSourceName(e.target.value)}
          placeholder="Source name, e.g. hubspot_main"
          style={{ minWidth: "180px" }}
        />
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}
        />
        <button className="btn btn-primary" onClick={handleUpload} disabled={isUploading} style={{ fontSize: "0.8rem" }}>
          <Upload size={14} />
          {isUploading ? "Uploading..." : "Upload CSV"}
        </button>
        <select className="select-input" value={sourceType} onChange={(e) => setSourceType(e.target.value as "hubspot" | "stripe")}>
          <option value="hubspot">HubSpot CRM</option>
          <option value="stripe">Stripe payments</option>
        </select>
        <button className="btn btn-secondary" onClick={handleRegisterSource} disabled={isRegistering} style={{ fontSize: "0.8rem" }}>
          <Plus size={14} />
          {isRegistering ? "Registering..." : "Add integration"}
        </button>
        <button className="btn btn-secondary" onClick={handleSyncSources} disabled={isSyncing} style={{ fontSize: "0.8rem" }}>
          <Play size={14} />
          {isSyncing ? "Syncing..." : "Sync API sources"}
        </button>
      </div>

      {message && (
        <p style={{ marginTop: "12px", fontSize: "0.82rem", color: "var(--accent-emerald)" }}>{message}</p>
      )}
      {error && (
        <p style={{ marginTop: "12px", fontSize: "0.82rem", color: "#fb7185" }}>{error}</p>
      )}
    </div>
  );
};
