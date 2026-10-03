import React, { useMemo, useState } from "react";
import { Database, Upload, Play, RefreshCw, Plus, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
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
      setError("Please specify a name for this data source.");
      return;
    }
    setIsRegistering(true);
    setError(null);
    setMessage(null);
    try {
      await createDataSource(name, sourceType);
      setMessage(
        `Successfully registered ${sourceType.toUpperCase()} source "${name}". Credentials are securely managed server-side. Trigger sync below to ingest live data.`
      );
      setSourceName("");
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not register data source");
    } finally {
      setIsRegistering(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a .csv file to import.");
      return;
    }
    setIsUploading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await uploadCsvFile(file, recordType, sourceName.trim() || "csv_import");
      setMessage(
        `Processed ${result.records_fetched} ${recordType} rows — ${result.records_inserted} inserted, ${result.records_duplicate} duplicates skipped, ${result.records_invalid} invalid rows flagged.`
      );
      setFile(null);
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "CSV ingestion failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSyncSources = async () => {
    if (syncableSources.length === 0) {
      setError("No active API integrations registered. Register HubSpot or Stripe first.");
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
            throw new Error(`${source.name}: ${run.error_message ?? "Pipeline run failed"}`);
          }
          totals.fetched += run.records_fetched;
          totals.inserted += run.records_inserted;
          totals.duplicate += run.records_duplicate;
          totals.invalid += run.records_invalid;
        }
      }
      setMessage(
        `Sync completed for ${syncableSources.length} source(s): fetched ${totals.fetched}, inserted ${totals.inserted}, ${totals.duplicate} duplicates, ${totals.invalid} invalid.`
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
      setError(err instanceof Error ? err.message : "Could not refresh pipeline status");
    }
  };

  return (
    <section aria-labelledby="sources-heading">
      {/* Notice Banner */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "12px",
          padding: "14px 18px",
          borderRadius: "12px",
          background: "var(--card-subtle-bg)",
          border: "1px solid var(--card-border)",
          marginBottom: "20px",
          fontSize: "0.85rem",
          color: "var(--text-primary)",
        }}
        role="note"
      >
        <ShieldCheck size={18} color="var(--accent-indigo)" style={{ flexShrink: 0, marginTop: "2px" }} aria-hidden="true" />
        <div>
          <strong>Enterprise Data Security:</strong> Third-party API credentials (Stripe, HubSpot, Shopify)
          are securely maintained in server environment variables. Registered sources connect to deterministic
          ingestion pipelines with automatic deduplication and validation.
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
            gap: "12px",
            marginBottom: "20px",
          }}
        >
          {[
            ["Registered Sources", sources.length],
            ["Pipeline Runs", summary.total_runs],
            ["Total Orders", summary.total_orders],
            ["Total Customers", summary.total_customers],
            ["Total Products", summary.total_products],
            ["Quality Issues", summary.total_quality_errors],
          ].map(([label, value]) => (
            <div
              key={String(label)}
              className="glass-card"
              style={{ padding: "14px 16px" }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, marginTop: "4px", color: "var(--text-primary)" }}>
                {value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Registered Sources List */}
      <div className="glass-card" style={{ padding: "20px 24px", marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 id="sources-heading" style={{ fontSize: "1rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
              <Database size={18} color="var(--accent-indigo)" /> Connected Data Sources
            </h3>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "4px 0 0" }}>
              Active platforms linked to your business analytics database.
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-secondary" onClick={handleRefreshSummary} style={{ fontSize: "0.8rem", padding: "7px 12px" }}>
              <RefreshCw size={14} /> Refresh
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSyncSources}
              disabled={isSyncing || syncableSources.length === 0}
              style={{ fontSize: "0.8rem", padding: "7px 14px", background: "var(--accent-indigo)", color: "#ffffff" }}
            >
              <Play size={14} />
              {isSyncing ? "Syncing..." : "Sync All Sources"}
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gap: "10px" }}>
          {sources.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              No sources registered yet. Add a platform or import a CSV file below.
            </div>
          ) : (
            sources.map((s) => (
              <div
                key={s.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "var(--card-subtle-bg)",
                  border: "1px solid var(--card-subtle-border)",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div>
                  <strong style={{ fontSize: "0.9rem" }}>{s.name}</strong>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                    Type: <code style={{ fontSize: "0.72rem" }}>{s.source_type}</code>
                    {s.description ? ` · ${s.description}` : ""}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="badge badge-positive" style={{ fontSize: "0.72rem" }}>
                    ● {s.is_active ? "Active" : "Paused"}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* CSV Upload & New Integration Actions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
        {/* CSV Import */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 8px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Upload size={16} color="var(--accent-indigo)" /> CSV File Ingestion
          </h4>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Import business transactions, customers, or products with automated schema validation.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Record Type
              </label>
              <select
                className="select-input"
                style={{ width: "100%" }}
                value={recordType}
                onChange={(e) => setRecordType(e.target.value as "customer" | "product" | "order")}
              >
                <option value="order">Orders (Sales &amp; Revenue)</option>
                <option value="customer">Customers (Profiles &amp; CRM)</option>
                <option value="product">Products (Catalog &amp; Inventory)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Source Name Tag
              </label>
              <input
                className="select-input"
                style={{ width: "100%" }}
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="e.g. offline_store_oct2026"
              />
            </div>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                CSV File
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                style={{ fontSize: "0.8rem", color: "var(--text-secondary)", width: "100%" }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={isUploading || !file}
              style={{ width: "100%", justifyContent: "center", background: "var(--accent-indigo)", color: "#ffffff" }}
            >
              <Upload size={15} />
              {isUploading ? "Validating & Ingesting…" : "Upload & Ingest CSV"}
            </button>
          </div>
        </div>

        {/* Register Platform Integration */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 8px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Plus size={16} color="var(--accent-indigo)" /> Connect New Integration
          </h4>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Add an external platform channel. Credentials are configured securely on the backend server.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Platform Type
              </label>
              <select
                className="select-input"
                style={{ width: "100%" }}
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value as "hubspot" | "stripe")}
              >
                <option value="hubspot">HubSpot CRM (Customers &amp; Products)</option>
                <option value="stripe">Stripe Payments (Orders &amp; Charges)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Integration Identifier
              </label>
              <input
                className="select-input"
                style={{ width: "100%" }}
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="e.g. stripe_primary"
              />
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                background: "var(--card-subtle-bg)",
                padding: "10px",
                borderRadius: "8px",
              }}
            >
              ℹ️ After registering, configure the corresponding API key in the server <code>.env</code> file, then click "Sync All Sources" to start pulling records.
            </div>
            <button
              className="btn btn-secondary"
              onClick={handleRegisterSource}
              disabled={isRegistering || !sourceName.trim()}
              style={{ width: "100%", justifyContent: "center" }}
            >
              <Plus size={15} />
              {isRegistering ? "Registering…" : "Register Platform Source"}
            </button>
          </div>
        </div>
      </div>

      {/* Status Feedback Messages */}
      {message && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "rgba(36, 132, 90, 0.12)",
            border: "1px solid rgba(36, 132, 90, 0.3)",
            fontSize: "0.85rem",
            color: "var(--accent-emerald)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
          role="status"
        >
          <CheckCircle2 size={16} />
          {message}
        </div>
      )}
      {error && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "rgba(195, 78, 83, 0.12)",
            border: "1px solid rgba(195, 78, 83, 0.3)",
            fontSize: "0.85rem",
            color: "var(--accent-rose)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
          role="alert"
        >
          <AlertTriangle size={16} />
          {error}
        </div>
      )}
    </section>
  );
};
