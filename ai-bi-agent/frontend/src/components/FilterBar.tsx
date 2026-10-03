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
  const presets = [
    { label: "Today", value: "today" },
    { label: "7 Days", value: "7d" },
    { label: "30 Days", value: "30d" },
    { label: "3 Months", value: "3m" },
    { label: "6 Months", value: "6m" },
    { label: "12 Months", value: "12m" },
    { label: "All Time", value: "all" },
    { label: "Custom Range", value: "custom" },
  ];

  return (
    <div className="glass-card" style={{ padding: "16px 24px", marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        {/* Date Presets */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-secondary)", fontSize: "0.85rem", fontWeight: 600, marginRight: "4px" }}>
            <Calendar size={16} /> Period:
          </div>
          {presets.map((p) => {
            const isActive = dateRange === p.value;
            return (
              <button
                key={p.value}
                onClick={() => onSelectDateRange(p.value)}
                style={{
                  background: isActive ? "var(--accent-indigo)" : "var(--card-subtle-bg)",
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  border: isActive ? "1px solid var(--accent-indigo)" : "1px solid var(--card-border)",
                  borderRadius: "8px",
                  padding: "6px 12px",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {p.label}
              </button>
            );
          })}
        </div>

        {/* Platform & Custom Dates & Refresh */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          {dateRange === "custom" && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <input
                type="date"
                className="date-input"
                value={startDate}
                onChange={(e) => onStartDateChange(e.target.value)}
              />
              <span style={{ color: "var(--text-muted)" }}>to</span>
              <input
                type="date"
                className="date-input"
                value={endDate}
                onChange={(e) => onEndDateChange(e.target.value)}
              />
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter size={16} color="var(--text-secondary)" />
            <select
              className="select-input"
              value={sourceName}
              onChange={(e) => onSelectSourceName(e.target.value)}
            >
              <option value="">All Data Sources</option>
              {sources.map((s) => (
                <option key={s.id} value={s.name}>
                  {s.name} ({s.source_type})
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn btn-secondary"
            onClick={onRefresh}
            disabled={isLoading}
            style={{ padding: "8px 12px" }}
            title="Refresh Analytics"
          >
            <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>
    </div>
  );
};
