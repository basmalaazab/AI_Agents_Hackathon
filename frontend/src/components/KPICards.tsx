import React from "react";
import { DollarSign, ShoppingBag, TrendingUp, Users, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { OverviewKPIs } from "../types/analytics";



interface KPICardsProps {
  data: OverviewKPIs | null;
  isLoading: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ data, isLoading }) => {
  if (isLoading || !data) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="glass-card" style={{ padding: "24px", minHeight: "130px", opacity: 0.6 }}>
            <div style={{ height: "16px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", width: "40%", marginBottom: "12px" }}></div>
            <div style={{ height: "32px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", width: "70%" }}></div>
          </div>
        ))}
      </div>
    );
  }

  const { kpis } = data;

  const cardConfig = [
    {
      title: "Total Revenue",
      metric: kpis.revenue,
      isCurrency: true,
      icon: DollarSign,
      color: "var(--accent-emerald)",
      bgGradient: "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(20, 184, 166, 0.05) 100%)",
    },
    {
      title: "Total Orders",
      metric: kpis.orders,
      isCurrency: false,
      icon: ShoppingBag,
      color: "var(--accent-indigo)",
      bgGradient: "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%)",
    },
    {
      title: "Average Order Value",
      metric: kpis.avg_order_value,
      isCurrency: true,
      icon: TrendingUp,
      color: "var(--accent-teal)",
      bgGradient: "linear-gradient(135deg, rgba(20, 184, 166, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%)",
    },
    {
      title: "Active Customers",
      metric: kpis.active_customers,
      isCurrency: false,
      icon: Users,
      color: "var(--accent-violet)",
      bgGradient: "linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%)",
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "24px" }}>
      {cardConfig.map((c) => {
        const Icon = c.icon;
        const val = c.metric.current;
        // Display the raw number. Currency symbol is intentionally omitted
        // because the backend does not guarantee USD conversion.
        const formattedVal = c.isCurrency
          ? val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : val.toLocaleString();

        const pct = c.metric.percentage_change;
        const isPositive = pct !== null && pct >= 0;

        return (
          <div key={c.title} className="glass-card animate-fade-in" style={{ padding: "20px 24px", position: "relative", overflow: "hidden" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)" }}>{c.title}</span>
              <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: c.bgGradient, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Icon size={20} color={c.color} />
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, fontFamily: "var(--font-heading)" }}>{formattedVal}</div>
              {pct !== null && (
                <div className={`badge ${isPositive ? "badge-positive" : "badge-negative"}`}>
                  {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                  {Math.abs(pct)}%
                </div>
              )}
            </div>

            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "8px" }}>
              {c.metric.previous !== null ? (
                <>vs {c.isCurrency ? c.metric.previous.toLocaleString("en-US", { minimumFractionDigits: 2 }) : c.metric.previous} prior period</>
              ) : (
                <>Overall metric</>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
