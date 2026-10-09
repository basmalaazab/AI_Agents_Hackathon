import React, { useEffect, useMemo, useState } from "react";
import { Database, Upload, Play, RefreshCw, Plus, CheckCircle2, AlertTriangle, ShieldCheck, Clock3, CircleHelp, PlugZap } from "lucide-react";
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
  const [isRefreshing, setIsRefreshing] = useState(false);
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

  const sourceTypeLabel = (type: string) => ({
    csv: "CSV file",
    stripe: "Stripe · test mode",
    hubspot: "HubSpot",
    mock_api: "Sample API",
    api: "API connection",
  }[type] ?? type.replaceAll("_", " "));

  const handleSyncOne = async (source: DataSourceInfo) => {
    setSyncingSourceId(source.id); setError(null); setMessage(null);
    try {
      const types: Array<"customer" | "product" | "order"> = source.source_type === "stripe" ? ["customer", "product", "order"] : ["customer", "product", "order"];
      let inserted = 0, invalid = 0, duplicate = 0;
      for (const type of types) {
        const run = await triggerPipeline(source.id, type);
        if (run.status === "failed") throw new Error(run.error_message || `${source.display_name || source.name} sync failed for ${type}.`);
        inserted += run.records_inserted; invalid += run.records_invalid; duplicate += run.records_duplicate;
      }
      const label = source.display_name || source.name;
      setMessage(inserted > 0
        ? `${label} is up to date: ${inserted} new records added${duplicate ? `, ${duplicate} already imported` : ""}${invalid ? `, ${invalid} need review` : ""}.`
        : `No new records found for ${label}${duplicate ? `; ${duplicate} were already imported` : ""}${invalid ? `; ${invalid} need review` : "."}`);
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
      setMessage(result.records_inserted > 0
        ? `Imported ${result.records_inserted} new ${recordType} record${result.records_inserted === 1 ? "" : "s"}${result.records_duplicate ? `; skipped ${result.records_duplicate} already imported` : ""}${result.records_invalid ? `; ${result.records_invalid} need review` : ""}.`
        : `No new ${recordType} records found${result.records_duplicate ? `; ${result.records_duplicate} were already imported` : ""}${result.records_invalid ? `; ${result.records_invalid} need review` : "."}`);
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
      setMessage(totals.inserted > 0
        ? `Updated ${syncableSources.length} platform${syncableSources.length === 1 ? "" : "s"}: ${totals.inserted} new records added${totals.duplicate ? `, ${totals.duplicate} already imported` : ""}${totals.invalid ? `, ${totals.invalid} need review` : ""}.`
        : `No new records found. Your data is already up to date${totals.duplicate ? `; ${totals.duplicate} were already imported` : ""}${totals.invalid ? `; ${totals.invalid} need review` : ""}.`);
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Pipeline sync failed");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRefreshSummary = async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const [stripeStatus, runs] = await Promise.all([
        fetchStripeReadiness(),
        fetchPipelineRuns(),
      ]);
      setStripeConfigured(stripeStatus.stripe.configured);
      setStripeSetupMessage(stripeStatus.stripe.message);
      setLatestRuns(runs);
      await fetchPipelineSummary();
      await onSourcesChanged();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not refresh pipeline status");
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <section aria-labelledby="sources-heading">
      <div className="sources-page-intro">
        <div>
          <span className="sources-eyebrow">YOUR WORKSPACE</span>
          <h2 id="sources-heading">Bring your business data together</h2>
          <p>Upload a CSV or sync a connected platform. Your dashboard updates after each import.</p>
        </div>
        {!readOnly && <span className="sources-step"><span>1</span> Add data <b>→</b> <span>2</span> Review insights</span>}
      </div>
      {readOnly && <div className="sources-viewer-note">You can explore the company data. Ask a manager to upload files or sync a platform.</div>}

      <details className="stripe-setup-help">
        <summary><ShieldCheck size={16} /> Stripe connection <span className={`source-setup-status ${stripeConfigured ? "ready" : "needs-setup"}`}>{stripeConfigured ? "Ready to sync" : "Setup needed"}</span></summary>
        <p>{stripeSetupMessage} Keep the secret key in the backend environment; never enter it in this page. Stripe is currently in test mode.</p>
      </details>

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
            ["Connected sources", sources.length],
            ["Orders", summary.total_orders],
            ["Products & customers", summary.total_products + summary.total_customers],
            ["Needs review", summary.total_quality_errors],
          ].map(([label, value]) => (
            <div
              key={String(label)}
              className="glass-card source-stat"
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{label}</div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, marginTop: "4px", color: "var(--text-primary)" }}>
                {value}
              </div>
              {label === "Needs review" && <small>{Number(value) === 0 ? "No data issues" : "Check imported rows"}</small>}
            </div>
          ))}
        </div>
      )}

      {/* Registered Sources List */}
      <div className="glass-card sources-connected-card" style={{ padding: "20px 24px", marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
              <Database size={18} color="var(--accent-indigo)" /> Your connections
            </h3>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "4px 0 0" }}>
              See what is connected and when it last updated.
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="btn btn-secondary" onClick={handleRefreshSummary} disabled={isRefreshing} style={{ fontSize: "0.8rem", padding: "7px 12px" }}>
              <RefreshCw size={14} /> {isRefreshing ? "Refreshing…" : "Refresh"}
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSyncSources}
              disabled={readOnly || isSyncing || syncableSources.length === 0}
              style={{ fontSize: "0.8rem", padding: "7px 14px", background: "var(--accent-indigo)", color: "var(--accent-on-primary)" }}
            >
              <Play size={14} />
              {isSyncing ? "Updating…" : "Sync all platforms"}
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gap: "10px" }}>
          {sources.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              No data sources yet. Start by uploading a CSV file below.
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
                  <div className="source-meta">
                    <span>{sourceTypeLabel(s.source_type)}</span>
                    {s.description ? <span>{s.description}</span> : null}
                    {getLatestRun(s.id) && <span className={`source-last-run ${getLatestRun(s.id)?.status === "failed" ? "failed" : ""}`}><Clock3 size={12} aria-hidden="true" />{getLatestRun(s.id)?.status === "failed" ? `Update failed · ${getLatestRun(s.id)?.error_message ?? "Check connection settings"}` : `Updated ${new Date(getLatestRun(s.id)!.started_at).toLocaleString()} · ${getLatestRun(s.id)?.records_inserted ?? 0} new`}</span>}
                  </div>
                </div>
                <div className="source-row-actions">
                  <span className={`source-status-pill ${s.is_active ? "active" : "paused"}`}>
                    <span aria-hidden="true">●</span> {s.is_active ? "Active" : "Paused"}
                  </span>
                  {s.source_type === "stripe" && <button className="btn btn-secondary" onClick={() => void handleSyncOne(s)} disabled={readOnly || !stripeConfigured || syncingSourceId === s.id} title={readOnly ? "Manager access required" : !stripeConfigured ? stripeSetupMessage : "Sync customers, products and payments"} style={{ fontSize: ".74rem", padding: "7px 10px" }}><RefreshCw size={13} />{syncingSourceId === s.id ? "Updating…" : "Sync now"}</button>}
                </div>
              </div>
            ))
          )}
        </div>
        {sources.filter((source) => source.source_type === "stripe").length > 1 && (
          <div className="stripe-duplicate-note"><AlertTriangle size={15} aria-hidden="true" /><span>There are multiple Stripe entries. Each uses the workspace Stripe key, so keep one entry per Stripe account to avoid syncing the same payments more than once.</span></div>
        )}
      </div>

      {/* CSV Upload & New Integration Actions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
        {/* CSV Import */}
        <div className="glass-card source-action-card primary" style={{ padding: "20px 24px" }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 8px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Upload size={16} color="var(--accent-indigo)" /> Upload a CSV file
          </h4>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Add sales, customer profiles, or products. Include stock quantities in product files to see low-stock alerts.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label htmlFor="csv-record-type" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                What does this file contain?
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
                Store or platform name <span className="field-optional">(optional)</span>
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
                Choose a CSV file
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
              {isUploading ? "Importing your file…" : "Upload and import"}
            </button>
          </div>
        </div>

        {/* Register Platform Integration */}
        <div className="glass-card source-action-card" style={{ padding: "20px 24px" }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 8px", display: "flex", alignItems: "center", gap: "8px" }}>
            <PlugZap size={16} color="var(--accent-indigo)" /> Connect a platform
          </h4>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Connect Stripe or HubSpot. Your workspace administrator must add credentials before the first sync.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label htmlFor="integration-platform" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                Choose a platform
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
                Connection name
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
              <><CircleHelp size={15} aria-hidden="true" /> Secret keys stay on the server. Never paste them into this page.</>
            </div>
            <button
              className="btn btn-secondary"
              onClick={handleRegisterSource}
              disabled={readOnly || isRegistering || !sourceName.trim()}
              style={{ width: "100%", justifyContent: "center" }}
            >
              <Plus size={15} />
              {isRegistering ? "Adding…" : "Add platform"}
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
