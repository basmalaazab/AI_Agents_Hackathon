import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import { FilterBar } from "./components/FilterBar";
import { KPICards } from "./components/KPICards";
import { RevenueTrendChart } from "./components/RevenueTrendChart";
import { CategoryBreakdownChart } from "./components/CategoryBreakdownChart";
import { TopPerformersTable } from "./components/TopPerformersTable";
import { AlertsPanel } from "./components/AlertsPanel";
import { AIContextModal } from "./components/AIContextModal";
import {
  fetchOverviewKPIs,
  fetchRevenueTrends,
  fetchSalesBreakdown,
  fetchCustomerAnalytics,
  fetchBusinessAlerts,
  fetchAIContext,
  getExportCSVUrl,
} from "./services/api";
import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "./types/analytics";

import { AlertCircle, RefreshCw } from "lucide-react";

export const App: React.FC = () => {
  // Theme state
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  // Filters state
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

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAIModalOpen, setIsAIModalOpen] = useState<boolean>(false);

  // Toggle theme
  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  // Fetch all analytics data
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
      ] = await Promise.all([
        fetchOverviewKPIs(dateRange, sourceName, startDate, endDate),
        fetchRevenueTrends(dateRange, sourceName, startDate, endDate),
        fetchSalesBreakdown(dateRange, sourceName, startDate, endDate),
        fetchCustomerAnalytics(dateRange, sourceName, startDate, endDate),
        fetchBusinessAlerts(dateRange, sourceName, startDate, endDate),
        fetchAIContext(dateRange, sourceName, startDate, endDate),
      ]);

      setOverview(overviewRes);
      setTrends(trendsRes);
      setBreakdown(breakdownRes);
      setCustomers(customersRes);
      setAlerts(alertsRes);
      setAiContextData(aiCtxRes);
    } catch (err: any) {
      console.error("Error loading analytics:", err);
      setError(
        err.message ||
          "Failed to connect to Analytics API at http://localhost:8000. Please check backend status."
      );
    } finally {
      setIsLoading(false);
    }
  }, [dateRange, sourceName, startDate, endDate]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const exportUrl = getExportCSVUrl(dateRange, sourceName, startDate, endDate);

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "24px 16px 48px" }}>
      {/* Header */}
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenAIModal={() => setIsAIModalOpen(true)}
        exportUrl={exportUrl}
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
      />

      {/* Error Fallback Banner */}
      {error && (
        <div
          className="glass-card"
          style={{
            padding: "16px 20px",
            marginBottom: "24px",
            borderColor: "rgba(244, 63, 94, 0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AlertCircle size={20} color="var(--accent-rose)" />
            <span style={{ fontSize: "0.9rem", color: "#fb7185" }}>{error}</span>
          </div>
          <button className="btn btn-secondary" onClick={loadAnalytics} style={{ fontSize: "0.8rem" }}>
            <RefreshCw size={14} /> Retry Connection
          </button>
        </div>
      )}

      {/* Business Alerts & Anomalies */}
      <AlertsPanel alerts={alerts} isLoading={isLoading} />

      {/* Overview Headline KPI Cards */}
      <KPICards data={overview} isLoading={isLoading} />

      {/* Revenue & Sales Time-Series Chart */}
      <RevenueTrendChart data={trends} isLoading={isLoading} />

      {/* Category & Channel Share Breakdown Charts */}
      <CategoryBreakdownChart data={breakdown} isLoading={isLoading} />

      {/* Top Performing Products & High LTV Customers */}
      <TopPerformersTable
        topProducts={breakdown?.top_products || []}
        topCustomers={customers?.top_customers || []}
        isLoading={isLoading}
      />

      {/* Person 3 AI Context Inspector Modal */}
      <AIContextModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        aiData={aiContextData}
      />
    </div>
  );
};

export default App;
