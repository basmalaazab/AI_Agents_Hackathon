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
  const styles = getComputedStyle(document.documentElement);
  const color = (token: string) => styles.getPropertyValue(token).trim();
  const chartColors = [
    color("--chart-primary"),
    color("--chart-secondary"),
    color("--chart-tertiary"),
    color("--chart-quaternary"),
  ];
  const gridColor = color("--chart-grid");
  const textMuted = color("--text-muted");
  const textSecondary = color("--text-secondary");
  const cardColor = color("--card-bg");

  // 1. Category Bar Chart
  const categoryLabels = by_category.map((c) => c.category);
  const categoryRevenues = by_category.map((c) => c.revenue);

  const barData = {
    labels: categoryLabels,
    datasets: [
      {
        label: "Revenue amount",
        data: categoryRevenues,
        backgroundColor: categoryLabels.map((_, index) => chartColors[index % chartColors.length]),
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
          label: (ctx: any) => ` Revenue amount: ${Number(ctx.raw).toLocaleString()}`,
        },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: textMuted } },
      y: { grid: { color: gridColor }, ticks: { color: textMuted, callback: (v: any) => Number(v).toLocaleString() } },
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
        backgroundColor: platformLabels.map((_, index) => chartColors[index % chartColors.length]),
        borderWidth: 2,
        borderColor: cardColor,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom" as const,
        labels: { color: textSecondary, font: { size: 12 }, padding: 16 },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => ` Revenue amount: ${Number(ctx.raw).toLocaleString()}`,
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
          Revenue contribution by category
        </p>
        <div style={{ height: "240px" }}>
          {by_category.length > 0 ? (
            <Bar data={barData} options={barOptions} />
          ) : (
            <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
          No category data is available for this period.
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
          No source data is available for this period.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
