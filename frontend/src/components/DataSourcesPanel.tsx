import React, { useEffect, useMemo, useState } from "react";
import { Database, Upload, Play, RefreshCw, Plus, CheckCircle2, AlertTriangle, ShieldCheck, Clock3 } from "lucide-react";
import {
  createDataSource,
  fetchPipelineSummary,
  triggerPipeline,
  uploadCsvFile,
  fetchStripeReadiness,
  fetchPipelineRuns,
  type PipelineRunInfo,
  type DataSourceInfo,
  type PipelineSummary,
} from "../services/api";

interface DataSourcesPanelProps {
  sources: DataSourceInfo[];
  summary: PipelineSummary | null;
  onSourcesChanged: () => Promise<void> | void;
  readOnly?: boolean;
}

export const DataSourcesPanel: React.FC<DataSourcesPanelProps> = ({
  sources,
  summary,
  onSourcesChanged,
  readOnly = false,
}) => {
  const [recordType, setRecordType] = useState<"customer" | "product" | "order">("order");
  const [sourceType, setSourceType] = useState<"hubspot" | "stripe">("stripe");
  const [sourceName, setSourceName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stripeConfigured, setStripeConfigured] = useState(false);
  const [stripeSetupMessage, setStripeSetupMessage] = useState("Checking Stripe setup…");
  const [latestRuns, setLatestRuns] = useState<PipelineRunInfo[]>([]);
  const [syncingSourceId, setSyncingSourceId] = useState<string | null>(null);

  const syncableSources = useMemo(
    () => sources.filter((s) => ["mock_api", "hubspot", "stripe"].includes(s.source_type) && s.is_active && (s.source_type !== "stripe" || stripeConfigured)),
    [sources, stripeConfigured]
  );

  useEffect(() => {
    fetchStripeReadiness().then(result => {
      setStripeConfigured(result.stripe.configured);
      setStripeSetupMessage(result.stripe.message);
    }).catch(() => setStripeSetupMessage("Could not check Stripe setup."));
    fetchPipelineRuns().then(setLatestRuns).catch(() => setLatestRuns([]));
  }, [sources]);

  const getLatestRun = (sourceId: string) => latestRuns
    .filter(run => run.data_source_id === sourceId)
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())[0];

  const handleSyncOne = async (source: DataSourceInfo) => {
    setSyncingSourceId(source.id); setError(null); setMessage(null);
    try {
      const types: Array<"customer" | "product" | "order"> = source.source_type === "stripe" ? ["customer", "product", "order"] : ["customer", "product", "order"];
      let fetched = 0, inserted = 0, invalid = 0;
      for (const type of types) {
        const run = await triggerPipeline(source.id, type);
        if (run.status === "failed") throw new Error(run.error_message || `${source.display_name || source.name} sync failed for ${type}.`);
        fetched += run.records_fetched; inserted += run.records_inserted; invalid += run.records_invalid;
      }
      setMessage(`${source.display_name || source.name} synced: ${fetched} records fetched, ${inserted} added, ${invalid} flagged for review.`);
      setLatestRuns(await fetchPipelineRuns());
      await onSourcesChanged();
    } catch (err) { setError(err instanceof Error ? err.message : `${source.display_name || source.name} sync failed.`); setLatestRuns(await fetchPipelineRuns().catch(() => latestRuns)); }
    finally { setSyncingSourceId(null); }
  };

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
        `${sourceType.toUpperCase()} source "${name}" is registered. Add backend credentials if required, then run a sync to check the connection.`
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
      setError("No enabled API sources are available to sync. Register a source and check its credentials first.");
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
            throw new Error(`${source.display_name || source.name}: ${run.error_message ?? "Pipeline run failed"}`);
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
      {readOnly && <div className="team-feedback" style={{ marginBottom: 16, borderColor: "var(--card-border)", color: "var(--text-secondary)" }}>You have viewer access. A manager can register sources, upload data, or start a sync.</div>}
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
          <strong>Stripe connection:</strong> {stripeSetupMessage} Keep the key in the backend environment, never in this browser.
          A successful sync validates access and writes a timestamped pipeline run. Imported records are validated and duplicates are skipped.
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
              <Database size={18} color="var(--accent-indigo)" /> Registered data sources
            </h3>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "4px 0 0" }}>
              Sources registered for import or synchronization.
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-secondary" onClick={handleRefreshSummary} style={{ fontSize: "0.8rem", padding: "7px 12px" }}>
              <RefreshCw size={14} /> Refresh
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSyncSources}
              disabled={readOnly || isSyncing || syncableSources.length === 0}
              style={{ fontSize: "0.8rem", padding: "7px 14px", background: "var(--accent-indigo)", color: "var(--accent-on-primary)" }}
            >
              <Play size={14} />
              {isSyncing ? "Syncing…" : "Sync enabled sources"}
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
                  <strong style={{ fontSize: "0.9rem" }}>{s.display_name || s.name}</strong>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                    Platform: <code style={{ fontSize: "0.72rem" }}>{s.source_type}</code>
                    {s.description ? ` · ${s.description}` : ""}
                    {getLatestRun(s.id) && <span style={{ display: "block", marginTop: 5, color: getLatestRun(s.id)?.status === "failed" ? "var(--badge-red-text)" : "var(--text-secondary)" }}><Clock3 size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />Last sync {new Date(getLatestRun(s.id)!.started_at).toLocaleString()} · {getLatestRun(s.id)!.status}{getLatestRun(s.id)?.status === "failed" ? ` · ${getLatestRun(s.id)?.error_message ?? "Check connector settings"}` : ` · ${getLatestRun(s.id)?.records_inserted ?? 0} records added`}</span>}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="badge badge-positive" style={{ fontSize: "0.72rem" }}>
                    ● {s.is_active ? "Enabled" : "Paused"}
                  </span>
                  {s.source_type === "stripe" && <button className="btn btn-secondary" onClick={() => void handleSyncOne(s)} disabled={readOnly || !stripeConfigured || syncingSourceId === s.id} title={readOnly ? "Manager access required" : !stripeConfigured ? stripeSetupMessage : "Sync customers, products and payments"} style={{ fontSize: ".74rem", padding: "7px 10px" }}><RefreshCw size={13} />{syncingSourceId === s.id ? "Syncing…" : "Sync Stripe"}</button>}
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
            Import transactions, customers, or products. Product CSVs can include `stock_quantity` and `reorder_point` to enable stock-risk estimates. Use the same source name as the sales data to match products with sales.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label htmlFor="csv-record-type" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Record Type
              </label>
              <select
                id="csv-record-type"
                className="select-input"
                style={{ width: "100%" }}
                value={recordType}
                disabled={readOnly}
                onChange={(e) => setRecordType(e.target.value as "customer" | "product" | "order")}
              >
                <option value="order">Orders (Sales &amp; Revenue)</option>
                <option value="customer">Customers (Profiles &amp; CRM)</option>
                <option value="product">Products &amp; stock levels</option>
              </select>
            </div>
            <div>
              <label htmlFor="csv-source-name" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Source name (optional)
              </label>
              <input
                id="csv-source-name"
                className="select-input"
                style={{ width: "100%" }}
                value={sourceName}
                disabled={readOnly}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="e.g. offline_store_oct2026"
              />
            </div>
            <div>
              <label htmlFor="csv-file" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                CSV File
              </label>
              <input
                id="csv-file"
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                disabled={readOnly}
                style={{ fontSize: "0.8rem", color: "var(--text-secondary)", width: "100%" }}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={readOnly || isUploading || !file}
              style={{ width: "100%", justifyContent: "center", background: "var(--accent-indigo)", color: "var(--accent-on-primary)" }}
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
            Add an external platform channel. Configure its credentials in the backend environment before starting a live sync.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label htmlFor="integration-platform" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Platform Type
              </label>
              <select
                id="integration-platform"
                className="select-input"
                style={{ width: "100%" }}
                value={sourceType}
                disabled={readOnly}
                onChange={(e) => setSourceType(e.target.value as "hubspot" | "stripe")}
              >
                <option value="hubspot">HubSpot CRM (Customers &amp; Products)</option>
                <option value="stripe">Stripe Payments (Orders &amp; Charges)</option>
              </select>
            </div>
            <div>
              <label htmlFor="integration-name" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Integration Identifier
              </label>
              <input
                id="integration-name"
                className="select-input"
                style={{ width: "100%" }}
                value={sourceName}
                disabled={readOnly}
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
            ℹ️ Add the required API key to the backend environment, then run a sync. Available records depend on the connector and your account permissions.
            </div>
            <button
              className="btn btn-secondary"
              onClick={handleRegisterSource}
              disabled={readOnly || isRegistering || !sourceName.trim()}
              style={{ width: "100%", justifyContent: "center" }}
            >
              <Plus size={15} />
              {isRegistering ? "Registering…" : "Register source"}
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
