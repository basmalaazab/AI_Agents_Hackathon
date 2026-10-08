import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import type { NavSection } from "./components/Header";
import { FilterBar } from "./components/FilterBar";
import { KPICards } from "./components/KPICards";
import { RevenueTrendChart } from "./components/RevenueTrendChart";
import { CategoryBreakdownChart } from "./components/CategoryBreakdownChart";
import { TopPerformersTable } from "./components/TopPerformersTable";
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
  getExportCSVUrl,
  type DataSourceInfo,
  type PipelineSummary,
} from "./services/api";
import { authenticatedFetch, clearAuthToken, getAuthToken, getCurrentUser, logout, type AuthUser } from "./services/auth";
import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "./types/analytics";

import { RefreshCw, WifiOff } from "lucide-react";

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

  const exportUrl = getExportCSVUrl(dateRange, sourceName, startDate, endDate);
  const handleExport = async () => {
    const response = await authenticatedFetch(exportUrl);
    if (!response.ok) throw new Error("Could not export CSV data.");
    const objectUrl = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = objectUrl; anchor.download = "clearview-analytics.csv"; anchor.click();
    URL.revokeObjectURL(objectUrl);
  };
  const apiOffline = !isLoading && error !== null;

  return (
    <div
      style={{ maxWidth: "1280px", margin: "0 auto", padding: "24px 16px 64px" }}
      role="main"
    >
      {/* ── Header + Navigation ───────────────────────────────── */}
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenAIModal={handleOpenAIModal}
        onExport={handleExport}
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
              <strong>Can’t reach the backend.</strong>{" "}
              <span style={{ color: "var(--text-secondary)" }}>{error}</span>
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
          {/* AI Briefing Panel — primary feature */}
          <AIBriefingPanel
            aiData={aiContextData}
            dateRange={dateRange}
            sourceName={sourceName}
            onOpenFullModal={handleOpenAIModal}
            apiOffline={apiOffline}
          />

          {/* Filter Bar */}
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
              ? `${aiContextData.currency_notice.unconverted_orders_excluded} non-USD orders are excluded from revenue totals because exchange-rate conversion is not configured.`
              : "Revenue totals are shown in USD. No exchange-rate conversion is applied to other currencies."}
          </p>

          {/* Business Alerts */}
          <AlertsPanel alerts={alerts} isLoading={isLoading} apiOffline={apiOffline} />
          <InventoryRiskPanel inventory={aiContextData?.inventory_risk} isLoading={isLoading} />

          {/* KPI Cards */}
          <KPICards data={overview} isLoading={isLoading} />

          {/* Revenue Trend Chart */}
          <RevenueTrendChart data={trends} isLoading={isLoading} />

          {/* Category & Platform Breakdown */}
          <CategoryBreakdownChart data={breakdown} isLoading={isLoading} />

          {/* Top Products & Top Customers */}
          <TopPerformersTable
            topProducts={breakdown?.top_products || []}
            topCustomers={customers?.top_customers || []}
            isLoading={isLoading}
          />
        </section>
      )}

      {/* ── AI ANALYST SECTION ───────────────────────────────── */}
      {activeSection === "analyst" && (
        <section aria-label="AI Analyst workspace">
          {/* Re-use the briefing panel as the entry point */}
          <AIBriefingPanel
            aiData={aiContextData}
            dateRange={dateRange}
            sourceName={sourceName}
            onOpenFullModal={handleOpenAIModal}
            apiOffline={apiOffline}
          />

          {/* Filter Bar */}
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
            Currency conversion is not applied. Filter to one source if your data uses different currencies.
          </p>

          {/* Prompt to open the full modal */}
          <div
            className="glass-card"
            style={{ padding: "32px", textAlign: "center" }}
          >
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "8px" }}>
              Explore your business data
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", marginBottom: "20px", maxWidth: "560px", margin: "0 auto 20px" }}>
              Review recommendations, investigate unusual changes, or ask focused questions about your business data.
            </p>
            <button
              className="btn btn-primary"
              onClick={handleOpenAIModal}
              style={{ fontSize: "0.9rem", padding: "10px 24px", background: "var(--accent-indigo)", color: "var(--accent-on-primary)" }}
            >
              Open AI Analyst
            </button>
          </div>
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
