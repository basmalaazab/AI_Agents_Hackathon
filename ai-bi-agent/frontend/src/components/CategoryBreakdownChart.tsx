import React from "react";
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import type { SalesBreakdownData } from "../types/analytics";


ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

interface CategoryBreakdownChartProps {
  data: SalesBreakdownData | null;
  isLoading: boolean;
}

export const CategoryBreakdownChart: React.FC<CategoryBreakdownChartProps> = ({ data, isLoading }) => {
  if (isLoading || !data) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", marginBottom: "24px" }}>
        <div className="glass-card" style={{ padding: "24px", minHeight: "280px" }}></div>
        <div className="glass-card" style={{ padding: "24px", minHeight: "280px" }}></div>
      </div>
    );
  }

  const { by_category, by_platform } = data;

  // 1. Category Bar Chart
  const categoryLabels = by_category.map((c) => c.category);
  const categoryRevenues = by_category.map((c) => c.revenue);

  const barData = {
    labels: categoryLabels,
    datasets: [
      {
        label: "Revenue ($)",
        data: categoryRevenues,
        backgroundColor: [
          "rgba(99, 102, 241, 0.8)",
          "rgba(20, 184, 166, 0.8)",
          "rgba(139, 92, 246, 0.8)",
          "rgba(244, 63, 94, 0.8)",
          "rgba(245, 158, 11, 0.8)",
        ],
        borderRadius: 8,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) => ` Revenue: $${ctx.raw.toLocaleString()}`,
        },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: "var(--text-muted)" } },
      y: { grid: { color: "rgba(148, 163, 184, 0.12)" }, ticks: { color: "var(--text-muted)", callback: (v: any) => `$${v}` } },
    },
  };

  // 2. Platform Doughnut Chart
  const platformLabels = by_platform.map((p) => p.platform.replace("_", " ").toUpperCase());
  const platformRevenues = by_platform.map((p) => p.revenue);

  const doughnutData = {
    labels: platformLabels,
    datasets: [
      {
        data: platformRevenues,
        backgroundColor: [
          "rgba(99, 102, 241, 0.85)",
          "rgba(16, 185, 129, 0.85)",
          "rgba(245, 158, 11, 0.85)",
          "rgba(244, 63, 94, 0.85)",
        ],
        borderWidth: 2,
        borderColor: "var(--card-bg)",
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom" as const,
        labels: { color: "var(--text-secondary)", font: { size: 12 }, padding: 16 },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => ` Revenue: $${ctx.raw.toLocaleString()}`,
        },
      },
    },
    cutout: "68%",
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", marginBottom: "24px" }}>
      {/* Category Bar Chart */}
      <div className="glass-card" style={{ padding: "24px" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "4px" }}>Revenue by Product Category</h3>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
          Sales distribution across product catalog
        </p>
        <div style={{ height: "240px" }}>
          {by_category.length > 0 ? (
            <Bar data={barData} options={barOptions} />
          ) : (
            <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
              No category data available
            </div>
          )}
        </div>
      </div>

      {/* Platform Doughnut Chart */}
      <div className="glass-card" style={{ padding: "24px" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "4px" }}>Sales Channel Share</h3>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
          Revenue split by source platform
        </p>
        <div style={{ height: "240px" }}>
          {by_platform.length > 0 ? (
            <Doughnut data={doughnutData} options={doughnutOptions} />
          ) : (
            <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
              No channel data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
