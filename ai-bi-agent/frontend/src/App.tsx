import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import type { NavSection } from "./components/Header";
import { FilterBar } from "./components/FilterBar";
import { KPICards } from "./components/KPICards";
import { RevenueTrendChart } from "./components/RevenueTrendChart";
import { CategoryBreakdownChart } from "./components/CategoryBreakdownChart";
import { TopPerformersTable } from "./components/TopPerformersTable";
import { AlertsPanel } from "./components/AlertsPanel";
import { AIChatCopilotModal } from "./components/AIChatCopilotModal";
import { AIBriefingPanel } from "./components/AIBriefingPanel";
import { DataSourcesPanel } from "./components/DataSourcesPanel";
import { ActivityPanel } from "./components/ActivityPanel";
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
import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "./types/analytics";

import { RefreshCw, WifiOff } from "lucide-react";

export const App: React.FC = () => {
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
        exportUrl={exportUrl}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* ── API Error / Offline Banner ────────────────────────── */}
      {error && (
        <div className="api-error-banner" role="alert" aria-live="assertive">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <WifiOff size={18} className="error-icon" aria-hidden="true" />
            <div>
              <strong>Backend not reachable.</strong>{" "}
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

          {/* Business Alerts */}
          <AlertsPanel alerts={alerts} isLoading={isLoading} apiOffline={apiOffline} />

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

          {/* Prompt to open the full modal */}
          <div
            className="glass-card"
            style={{ padding: "32px", textAlign: "center" }}
          >
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "8px" }}>
              Explore Deep Analytical Reasoning &amp; Diagnostics
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", marginBottom: "20px", maxWidth: "560px", margin: "0 auto 20px" }}>
              Open the full AI Business Analyst console for Strategic Action Plans, Anomaly Root-Cause Analysis,
              and Safe Read-Only SQL Inspection.
            </p>
            <button
              className="btn btn-primary"
              onClick={handleOpenAIModal}
              style={{ fontSize: "0.9rem", padding: "10px 24px", background: "var(--accent-indigo)", color: "#ffffff" }}
            >
              Launch Full AI Analyst
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
        />
      )}

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

export default App;
