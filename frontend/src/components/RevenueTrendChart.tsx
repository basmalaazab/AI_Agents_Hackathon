import React, { useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { RevenueTrendPoint } from "../types/analytics";


ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface RevenueTrendChartProps {
  data: RevenueTrendPoint[];
  isLoading: boolean;
}

export const RevenueTrendChart: React.FC<RevenueTrendChartProps> = ({ data, isLoading }) => {
  const [activeTab, setActiveTab] = useState<"revenue" | "orders">("revenue");

  if (isLoading || !data || data.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "24px", marginBottom: "24px", minHeight: "350px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)" }}>{isLoading ? "Loading trend data..." : "No trend data available for the selected period."}</p>
      </div>
    );
  }

  const labels = data.map((d) => d.date);
  const isRevenue = activeTab === "revenue";
  const datasetValues = data.map((d) => (isRevenue ? d.revenue : d.orders));

  const chartData = {
    labels,
    datasets: [
      {
        fill: true,
        label: isRevenue ? "Revenue" : "Completed Orders",
        data: datasetValues,
        borderColor: isRevenue ? "#6366f1" : "#14b8a6",
        backgroundColor: isRevenue
          ? "rgba(99, 102, 241, 0.15)"
          : "rgba(20, 184, 166, 0.15)",
        tension: 0.35,
        borderWidth: 2.5,
        pointRadius: data.length < 35 ? 3 : 0,
        pointHoverRadius: 6,
        pointBackgroundColor: isRevenue ? "#8b5cf6" : "#10b981",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#f8fafc",
        bodyColor: "#cbd5e1",
        borderColor: "rgba(255, 255, 255, 0.1)",
        borderWidth: 1,
        padding: 12,
        boxPadding: 6,
        callbacks: {
          label: (context: any) => {
            const val = context.raw;
            return isRevenue ? ` Revenue: ${val.toLocaleString()}` : ` Orders: ${val}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: "rgba(148, 163, 184, 0.1)",
        },
        ticks: {
          color: "var(--text-muted)",
          font: { size: 11 },
          maxRotation: 45,
        },
      },
      y: {
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
        ticks: {
          color: "var(--text-muted)",
          font: { size: 11 },
          callback: (value: any) => (isRevenue ? value.toLocaleString() : value),
        },
      },
    },
  };

  return (
    <div className="glass-card" style={{ padding: "24px", marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Performance Trends Over Time</h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Daily revenue and order volume trajectory
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", background: "var(--card-subtle-bg)", border: "1px solid var(--card-border)", padding: "4px", borderRadius: "10px" }}>
          <button
            onClick={() => setActiveTab("revenue")}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              border: "none",
              background: isRevenue ? "var(--accent-indigo)" : "transparent",
              color: isRevenue ? "#fff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            Revenue ($)
          </button>
          <button
            onClick={() => setActiveTab("orders")}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              border: "none",
              background: !isRevenue ? "var(--accent-teal)" : "transparent",
              color: !isRevenue ? "#fff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            Order Volume
          </button>
        </div>
      </div>

      <div style={{ height: "320px", position: "relative" }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};
