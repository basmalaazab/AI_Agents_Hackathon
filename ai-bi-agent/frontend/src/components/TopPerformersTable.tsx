import React, { useState } from "react";
import { Package, Users, Search } from "lucide-react";
import type { TopProduct, TopCustomer } from "../types/analytics";



interface TopPerformersTableProps {
  topProducts: TopProduct[];
  topCustomers: TopCustomer[];
  isLoading: boolean;
}

export const TopPerformersTable: React.FC<TopPerformersTableProps> = ({
  topProducts,
  topCustomers,
  isLoading,
}) => {
  const [tab, setTab] = useState<"products" | "customers">("products");
  const [searchTerm, setSearchTerm] = useState("");

  if (isLoading) {
    return (
      <div className="glass-card" style={{ padding: "24px", marginBottom: "24px", minHeight: "250px" }}>
        <p style={{ color: "var(--text-muted)" }}>Loading top performers...</p>
      </div>
    );
  }

  const isProducts = tab === "products";

  const q = searchTerm.toLowerCase();
  const filteredProducts = topProducts.filter((p) => {
    const name = (p.name || "").toLowerCase();
    const sku = (p.sku || "").toLowerCase();
    const category = (p.category || "").toLowerCase();
    return name.includes(q) || sku.includes(q) || category.includes(q);
  });

  const filteredCustomers = topCustomers.filter((c) => {
    const name = (c.name || "").toLowerCase();
    const email = (c.email || "").toLowerCase();
    return name.includes(q) || email.includes(q);
  });

  return (
    <div className="glass-card" style={{ padding: "24px", marginBottom: "24px" }}>
      {/* Header & Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            onClick={() => setTab("products")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 16px",
              borderRadius: "10px",
              border: "none",
              background: isProducts ? "var(--accent-indigo)" : "rgba(255,255,255,0.05)",
              color: isProducts ? "#fff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: "pointer",
            }}
          >
            <Package size={16} /> Top Products
          </button>

          <button
            onClick={() => setTab("customers")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 16px",
              borderRadius: "10px",
              border: "none",
              background: !isProducts ? "var(--accent-indigo)" : "rgba(255,255,255,0.05)",
              color: !isProducts ? "#fff" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: "pointer",
            }}
          >
            <Users size={16} /> Top Customers (LTV)
          </button>
        </div>

        <div style={{ position: "relative" }}>
          <Search size={16} color="var(--text-muted)" style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }} />
          <input
            type="text"
            placeholder={`Search ${isProducts ? "products..." : "customers..."}`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="select-input"
            style={{ paddingLeft: "36px", width: "220px" }}
          />
        </div>
      </div>

      {/* Table Content */}
      <div style={{ overflowX: "auto" }}>
        {isProducts ? (
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--text-muted)" }}>
                <th style={{ padding: "12px 16px" }}>Rank</th>
                <th style={{ padding: "12px 16px" }}>Product Name</th>
                <th style={{ padding: "12px 16px" }}>SKU</th>
                <th style={{ padding: "12px 16px" }}>Category</th>
                <th style={{ padding: "12px 16px" }}>Units Sold</th>
                <th style={{ padding: "12px 16px" }}>Order Count</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Total Revenue</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((p, idx) => (
                <tr key={p.name + idx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                  <td style={{ padding: "12px 16px", fontWeight: 700, color: "var(--accent-indigo)" }}>#{idx + 1}</td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>{p.name}</td>
                  <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{p.sku}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className="badge badge-warning">{p.category}</span>
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>{p.units_sold}</td>
                  <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{p.order_count}</td>
                  <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 700, color: "var(--accent-emerald)" }}>
                    ${p.revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
              {filteredProducts.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No products matched your search or period.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--text-muted)" }}>
                <th style={{ padding: "12px 16px" }}>Rank</th>
                <th style={{ padding: "12px 16px" }}>Customer Name</th>
                <th style={{ padding: "12px 16px" }}>Email</th>
                <th style={{ padding: "12px 16px" }}>Channel</th>
                <th style={{ padding: "12px 16px" }}>Orders Placed</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Lifetime Value (LTV)</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((c, idx) => (
                <tr key={c.customer_id + idx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                  <td style={{ padding: "12px 16px", fontWeight: 700, color: "var(--accent-violet)" }}>#{idx + 1}</td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>{c.name}</td>
                  <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{c.email}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className="badge badge-positive">{c.source_name}</span>
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>{c.order_count}</td>
                  <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 700, color: "var(--accent-emerald)" }}>
                    ${c.lifetime_value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
              {filteredCustomers.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
                    No customer data found for the selected period.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
