import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import type { NavSection } from "./components/Header";
import { FilterBar } from "./components/FilterBar";
import { KPICards } from "./components/KPICards";
import { RevenueTrendChart } from "./components/RevenueTrendChart";
import { CategoryBreakdownChart } from "./components/CategoryBreakdownChart";
import { TopPerformersTable } from "./components/TopPerformersTable";
import { RFMSegmentsPanel } from "./components/RFMSegmentsPanel";
import { AlertsPanel } from "./components/AlertsPanel";
import { InventoryRiskPanel } from "./components/InventoryRiskPanel";
import { AIChatCopilotModal } from "./components/AIChatCopilotModal";
import { AIBriefingPanel } from "./components/AIBriefingPanel";
import { DataSourcesPanel } from "./components/DataSourcesPanel";
import { ActivityPanel } from "./components/ActivityPanel";
import { TeamPanel } from "./components/TeamPanel";
import { AuthScreen } from "./components/AuthScreen";
import {
  fetchOverviewKPIs,
  fetchRevenueTrends,
  fetchSalesBreakdown,
  fetchCustomerAnalytics,
  fetchBusinessAlerts,
  fetchAIContext,
  fetchDataSources,
  fetchPipelineSummary,
  getExportXLSXUrl,
  type DataSourceInfo,
  type PipelineSummary,
} from "./services/api";
import { authenticatedFetch, clearAuthToken, getAuthToken, getCurrentUser, logout, type AuthUser } from "./services/auth";
import { fetchRecommendations } from "./services/agentApi";
import type { StrategicRecommendation } from "./types/agent";
import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "./types/analytics";

import { RefreshCw, WifiOff, ArrowRight, BarChart3, Sparkles } from "lucide-react";

const DashboardApp: React.FC<{ user: AuthUser; onLogout: () => void }> = ({ user, onLogout }) => {
  // Theme state — light is the default for a professional SaaS look
  const [theme, setTheme] = useState<"dark" | "light">("light");

  // Navigation
  const [activeSection, setActiveSection] = useState<NavSection>("overview");

  // Filters
  const [dateRange, setDateRange] = useState<string>("30d");
  const [sourceName, setSourceName] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  // Data states
  const [overview, setOverview] = useState<OverviewKPIs | null>(null);
  const [trends, setTrends] = useState<RevenueTrendPoint[]>([]);
  const [breakdown, setBreakdown] = useState<SalesBreakdownData | null>(null);
  const [customers, setCustomers] = useState<CustomerAnalyticsData | null>(null);
  const [alerts, setAlerts] = useState<BusinessAlert[]>([]);
  const [aiContextData, setAiContextData] = useState<any>(null);
  const [dataSources, setDataSources] = useState<DataSourceInfo[]>([]);
  const [pipelineSummary, setPipelineSummary] = useState<PipelineSummary | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAIModalOpen, setIsAIModalOpen] = useState<boolean>(false);
  const [printRecommendations, setPrintRecommendations] = useState<StrategicRecommendation[] | null>(null);

  // Apply theme to document
  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  // Set initial theme on mount
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, []);

  // Open AI Analyst modal directly
  const handleOpenAIModal = () => {
    setIsAIModalOpen(true);
  };

  const handleOpenDataSources = () => setActiveSection("sources");

  const handlePrintReport = async () => {
    let recommendations: StrategicRecommendation[] = [];
    try { recommendations = (await fetchRecommendations(dateRange, sourceName)).recommendations; }
    catch (err) { console.error("Could not load AI recommendations for the printable report", err); }
    window.addEventListener("afterprint", () => setPrintRecommendations(null), { once: true });
    setPrintRecommendations(recommendations);
    window.setTimeout(() => window.print(), 100);
  };

  // Fetch all analytics and data source metadata
  const loadAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [
        overviewRes,
        trendsRes,
        breakdownRes,
        customersRes,
        alertsRes,
        aiCtxRes,
        sourcesRes,
        summaryRes,
      ] = await Promise.all([
        fetchOverviewKPIs(dateRange, sourceName, startDate, endDate),
        fetchRevenueTrends(dateRange, sourceName, startDate, endDate),
        fetchSalesBreakdown(dateRange, sourceName, startDate, endDate),
        fetchCustomerAnalytics(dateRange, sourceName, startDate, endDate),
        fetchBusinessAlerts(dateRange, sourceName, startDate, endDate),
        fetchAIContext(dateRange, sourceName, startDate, endDate),
        fetchDataSources().catch(() => []),
        fetchPipelineSummary().catch(() => null),
      ]);

      setOverview(overviewRes);
      setTrends(trendsRes);
      setBreakdown(breakdownRes);
      setCustomers(customersRes);
      setAlerts(alertsRes);
      setAiContextData(aiCtxRes);
      setDataSources(sourcesRes);
      setPipelineSummary(summaryRes);
    } catch (err: any) {
      console.error("Error loading analytics:", err);
      setError(
        err.message ||
          "Could not connect to the analytics backend at http://localhost:8000. Check that the backend is running."
      );
    } finally {
      setIsLoading(false);
    }
  }, [dateRange, sourceName, startDate, endDate]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const handleIngestComplete = async () => {
    await loadAnalytics();
  };

  const exportUrl = getExportXLSXUrl(dateRange, sourceName, startDate, endDate);
  const handleExport = async () => {
    const response = await authenticatedFetch(exportUrl);
    if (!response.ok) throw new Error("Could not export the Excel report.");
    const objectUrl = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = objectUrl; anchor.download = `clearview-bi-report-${dateRange}.xlsx`; anchor.click();
    URL.revokeObjectURL(objectUrl);
  };
  const apiOffline = !isLoading && error !== null;

  return (
    <div
      className="dashboard-shell"
      style={{ maxWidth: "1280px", margin: "0 auto", padding: "24px 16px 64px" }}
      role="main"
    >
      {/* ── Header + Navigation ───────────────────────────────── */}
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenAIModal={handleOpenAIModal}
        onExport={handleExport}
        onPrintReport={handlePrintReport}
        user={user}
        onLogout={onLogout}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* ── API Error / Offline Banner ────────────────────────── */}
      {error && (
        <div className="api-error-banner" role="alert" aria-live="assertive">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <WifiOff size={18} className="error-icon" aria-hidden="true" />
            <div>
              <strong>Your dashboard couldn’t load.</strong>{" "}
              <span style={{ color: "var(--text-secondary)" }}>Check your connection and try again.</span>
              <details className="api-error-details">
                <summary>Technical details</summary>
                <span>{error}</span>
              </details>
            </div>
          </div>
          <button
            className="btn btn-secondary"
            onClick={loadAnalytics}
            style={{ fontSize: "0.8rem", flexShrink: 0 }}
            aria-label="Retry connecting to analytics backend"
          >
            <RefreshCw size={14} aria-hidden="true" /> Retry
          </button>
        </div>
      )}

      {/* ── OVERVIEW SECTION ─────────────────────────────────── */}
      {activeSection === "overview" && (
        <section aria-label="Business overview">
          <div className="page-intro">
            <div>
              <span className="page-eyebrow">YOUR BUSINESS</span>
              <h2>Business overview</h2>
              <p>Track sales, customers, and inventory in one place.</p>
            </div>
          </div>
          {/* Keep the landing page focused on a few decisions at a time. */}
          <FilterBar
            dateRange={dateRange}
            onSelectDateRange={setDateRange}
            sourceName={sourceName}
            onSelectSourceName={setSourceName}
            startDate={startDate}
            onStartDateChange={setStartDate}
            endDate={endDate}
            onEndDateChange={setEndDate}
            onRefresh={loadAnalytics}
            isLoading={isLoading}
            sources={dataSources}
          />
          <p className="currency-note" role="note">
            {aiContextData?.currency_notice?.unconverted_orders_excluded > 0
              ? `${aiContextData.currency_notice.unconverted_orders_excluded} orders use currencies without a configured USD rate and are excluded from revenue totals.`
              : <>Revenue is shown in USD using daily rates where available. Rate source: <a href="https://www.exchangerate-api.com" target="_blank" rel="noreferrer">ExchangeRate-API</a>.</>}
          </p>

          {/* KPI Cards */}
          <KPICards data={overview} isLoading={isLoading} />

          {/* Business Alerts */}
          <AlertsPanel alerts={alerts} isLoading={isLoading} apiOffline={apiOffline} />

          <div className="overview-actions">
            <button className="overview-action" onClick={() => setActiveSection("performance")}>
              <span className="overview-action-icon"><BarChart3 size={19} /></span>
              <span><strong>Explore performance</strong><small>Sales trends, top products, and customer activity</small></span>
              <ArrowRight size={17} />
            </button>
            <button className="overview-action" onClick={() => setActiveSection("analyst")}>
              <span className="overview-action-icon ai"><Sparkles size={19} /></span>
              <span><strong>Ask the AI Analyst</strong><small>Get answers grounded in your selected data</small></span>
              <ArrowRight size={17} />
            </button>
          </div>
        </section>
      )}

      {activeSection === "performance" && (
        <section aria-label="Business performance">
          <div className="page-intro">
            <div>
              <span className="page-eyebrow">DETAILED ANALYTICS</span>
              <h2>Performance</h2>
              <p>Explore trends, product results, customers, and stock risk.</p>
            </div>
          </div>
          <FilterBar
            dateRange={dateRange}
            onSelectDateRange={setDateRange}
            sourceName={sourceName}
            onSelectSourceName={setSourceName}
            startDate={startDate}
            onStartDateChange={setStartDate}
            endDate={endDate}
            onEndDateChange={setEndDate}
            onRefresh={loadAnalytics}
            isLoading={isLoading}
            sources={dataSources}
          />
          <RevenueTrendChart data={trends} isLoading={isLoading} />
          <CategoryBreakdownChart data={breakdown} isLoading={isLoading} />
          <InventoryRiskPanel inventory={aiContextData?.inventory_risk} isLoading={isLoading} />
          <TopPerformersTable
            topProducts={breakdown?.top_products || []}
            topCustomers={customers?.top_customers || []}
            isLoading={isLoading}
          />
          <RFMSegmentsPanel segments={customers?.rfm_segmentation?.segments} isLoading={isLoading} />
        </section>
      )}

      {/* ── AI ANALYST SECTION ───────────────────────────────── */}
      {activeSection === "analyst" && (
        <section aria-label="AI Analyst workspace">
          <div className="page-intro">
            <div>
              <span className="page-eyebrow">ASK IN PLAIN LANGUAGE</span>
              <h2>AI Business Analyst</h2>
              <p>Ask about sales, customers, products, and trends in your business data.</p>
            </div>
          </div>
          <FilterBar
            dateRange={dateRange}
            onSelectDateRange={setDateRange}
            sourceName={sourceName}
            onSelectSourceName={setSourceName}
            startDate={startDate}
            onStartDateChange={setStartDate}
            endDate={endDate}
            onEndDateChange={setEndDate}
            onRefresh={loadAnalytics}
            isLoading={isLoading}
            sources={dataSources}
          />
          <p className="currency-note" role="note">Revenue is shown in USD using daily rates where available. Rate source: <a href="https://www.exchangerate-api.com" target="_blank" rel="noreferrer">ExchangeRate-API</a>.</p>
          <AIBriefingPanel
            aiData={aiContextData}
            dateRange={dateRange}
            sourceName={sourceName}
            onOpenFullModal={handleOpenAIModal}
            onOpenDataSources={handleOpenDataSources}
            apiOffline={apiOffline}
          />
        </section>
      )}

      {/* ── DATA SOURCES SECTION ─────────────────────────────── */}
      {activeSection === "sources" && (
        <DataSourcesPanel
          sources={dataSources}
          summary={pipelineSummary}
          onSourcesChanged={handleIngestComplete}
          readOnly={user.role === "viewer"}
        />
      )}

      {activeSection === "team" && <TeamPanel user={user} />}

      {/* ── ACTIVITY SECTION ─────────────────────────────────── */}
      {activeSection === "activity" && (
        <ActivityPanel apiOffline={apiOffline} />
      )}

      {/* ── AI Full Analyst Modal ────────────────────────────── */}
      <AIChatCopilotModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        aiData={aiContextData}
        dateRange={dateRange}
        sourceName={sourceName}
      />
      {printRecommendations && <article className="executive-print-report">
        <header><div className="print-brand-mark">CB</div><div><p className="print-eyebrow">CLEARVIEW BI · EXECUTIVE REPORT</p><h1>Business performance summary</h1><p>{dateRange} · {sourceName || "All connected sources"} · Generated {new Date().toLocaleDateString()}</p></div></header>
        <section className="print-kpis">
          {[ ["Revenue", overview?.kpis.revenue.current, "USD"], ["Orders", overview?.kpis.orders.current, ""], ["Average order value", overview?.kpis.avg_order_value.current, "USD"], ["Active customers", overview?.kpis.active_customers.current, ""] ].map(([label, value, unit]) => <div key={String(label)}><small>{label}</small><strong>{unit === "USD" ? `$${Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}` : Number(value || 0).toLocaleString()}</strong></div>)}
        </section>
        <section><h2>Key alerts</h2>{alerts.length ? <ul>{alerts.slice(0, 5).map((alert) => <li key={alert.id}><strong>{alert.title}</strong>: {alert.message}</li>)}</ul> : <p>No active alerts for this period.</p>}</section>
        <section><h2>Top products</h2><ol>{(breakdown?.top_products || []).slice(0, 5).map((product) => <li key={product.sku || product.name}>{product.name} — ${Number(product.revenue).toLocaleString("en-US", { minimumFractionDigits: 2 })}</li>)}</ol></section>
        <section><h2>AI recommendations</h2>{printRecommendations.length ? printRecommendations.slice(0, 5).map((recommendation) => <div className="print-recommendation" key={recommendation.id}><h3>{recommendation.title} <small>{recommendation.priority}</small></h3><p>{recommendation.data_justification}</p><ul>{recommendation.action_steps.slice(0, 3).map((step) => <li key={step}>{step}</li>)}</ul></div>) : <p>Recommendations are unavailable. Open the AI Analyst to review this period.</p>}</section>
        <footer>Prepared by Clearview BI · Revenue includes orders with a supported USD conversion rate. Exchange-rate source: ExchangeRate-API (daily reference rates).</footer>
      </article>}
    </div>
  );
};

export const App: React.FC = () => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(getAuthToken()));
  useEffect(() => {
    if (!getAuthToken()) return;
    getCurrentUser().then(setUser).catch(() => clearAuthToken()).finally(() => setCheckingSession(false));
  }, []);
  const handleLogout = async () => { await logout(); setUser(null); };
  if (checkingSession) return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>Loading your workspace…</main>;
  if (!user) return <AuthScreen onAuthenticated={setUser} />;
  return <DashboardApp user={user} onLogout={handleLogout} />;
};

export default App;
