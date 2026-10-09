import React from "react";
import { Calendar, Filter, RefreshCw } from "lucide-react";
import type { DataSourceInfo } from "../services/api";

interface FilterBarProps {
  dateRange: string;
  onSelectDateRange: (range: string) => void;
  sourceName: string;
  onSelectSourceName: (source: string) => void;
  sources: DataSourceInfo[];
  startDate: string;
  onStartDateChange: (date: string) => void;
  endDate: string;
  onEndDateChange: (date: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  dateRange,
  onSelectDateRange,
  sourceName,
  onSelectSourceName,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
  onRefresh,
  isLoading,
  sources,
}) => {
  return (
    <div className="glass-card filter-toolbar">
      <label className="filter-control">
        <span><Calendar size={15} /> Period</span>
        <select className="select-input" aria-label="Choose date range" value={dateRange} onChange={(e) => onSelectDateRange(e.target.value)}>
          <option value="today">Today</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="3m">Last 3 months</option>
          <option value="6m">Last 6 months</option>
          <option value="12m">Last 12 months</option>
          <option value="all">All time</option>
          <option value="custom">Custom dates</option>
        </select>
      </label>

      <label className="filter-control source-filter-control">
        <span><Filter size={15} /> Data source</span>
        <select
          className="select-input"
          aria-label="Filter by data source"
          value={sourceName}
          onChange={(e) => onSelectSourceName(e.target.value)}
        >
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s.id} value={s.name}>
              {s.display_name || s.name} · {s.source_type === "csv" ? "CSV" : s.source_type === "stripe" ? "Stripe" : s.source_type}
            </option>
          ))}
        </select>
      </label>

      {dateRange === "custom" && (
        <div className="filter-custom-dates" aria-label="Custom date range">
          <label><span>From</span><input type="date" className="date-input" aria-label="Start date" value={startDate} onChange={(e) => onStartDateChange(e.target.value)} /></label>
          <label><span>To</span><input type="date" className="date-input" aria-label="End date" value={endDate} onChange={(e) => onEndDateChange(e.target.value)} /></label>
        </div>
      )}

      <button className="btn btn-secondary filter-refresh" onClick={onRefresh} disabled={isLoading} aria-label={isLoading ? "Refreshing analytics" : "Refresh analytics"}>
        <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} /> <span>{isLoading ? "Refreshing" : "Refresh"}</span>
      </button>
    </div>
  );
};
