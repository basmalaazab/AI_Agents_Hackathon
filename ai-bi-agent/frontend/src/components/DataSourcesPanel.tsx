import React, { useMemo, useState } from "react";
import { Database, Upload, Play, RefreshCw } from "lucide-react";
import {
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
  const [sourceName, setSourceName] = useState("csv_upload");
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mockSources = useMemo(
    () => sources.filter((s) => s.source_type === "mock_api" && s.is_active),
    [sources]
  );

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

  const handleSyncMock = async () => {
    if (mockSources.length === 0) {
      setError("No active mock API source is registered. Start the backend and mock API, then refresh.");
      return;
    }
    setIsSyncing(true);
    setError(null);
    setMessage(null);
    try {
      const types: Array<"customer" | "product" | "order"> = ["customer", "product", "order"];
      const totals = { fetched: 0, inserted: 0, duplicate: 0, invalid: 0 };
      for (const source of mockSources) {
        for (const type of types) {
          const run = await triggerPipeline(source.id, type);
          totals.fetched += run.records_fetched;
          totals.inserted += run.records_inserted;
          totals.duplicate += run.records_duplicate;
          totals.invalid += run.records_invalid;
        }
      }
      setMessage(
        `Synced mock platforms — fetched ${totals.fetched}, inserted ${totals.inserted}, duplicates ${totals.duplicate}, invalid ${totals.invalid}.`
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
            Ingest CRM / sales / POS-style CSVs and sync the mock e-commerce platform into one database.
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
          placeholder="Source name, e.g. pos_terminal"
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
        <button className="btn btn-secondary" onClick={handleSyncMock} disabled={isSyncing} style={{ fontSize: "0.8rem" }}>
          <Play size={14} />
          {isSyncing ? "Syncing..." : "Sync mock platform"}
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
