import React, { useState } from "react";
import { Boxes, CircleAlert, ClipboardList, Copy, Check } from "lucide-react";
import { prepareInventoryReorderDraft } from "../services/agentApi";
import type { InventoryReorderDraft } from "../services/agentApi";

interface InventoryProduct {
  name: string;
  sku: string | null;
  stock_quantity: number;
  reorder_point: number | null;
  units_sold_last_30d: number;
  estimated_days_of_cover: number | null;
  at_risk: boolean;
  source_name: string;
}

interface InventoryRisk {
  available: boolean;
  products_with_stock_data: number;
  at_risk_count: number;
  products: InventoryProduct[];
  method: string;
}

export const InventoryRiskPanel: React.FC<{ inventory?: InventoryRisk; isLoading: boolean }> = ({
  inventory,
  isLoading,
}) => {
  const [selectedProduct, setSelectedProduct] = useState<InventoryProduct | null>(null);
  const [leadTimeDays, setLeadTimeDays] = useState("");
  const [targetCoverDays, setTargetCoverDays] = useState("14");
  const [draft, setDraft] = useState<InventoryReorderDraft | null>(null);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [isPreparing, setIsPreparing] = useState(false);
  const [copied, setCopied] = useState(false);

  if (isLoading) return null;

  const handlePrepareDraft = async () => {
    if (!selectedProduct || leadTimeDays === "") return;
    setIsPreparing(true);
    setDraftError(null);
    setDraft(null);
    try {
      const result = await prepareInventoryReorderDraft({
        productName: selectedProduct.name,
        productSku: selectedProduct.sku,
        sourceName: selectedProduct.source_name,
        supplierLeadTimeDays: Number(leadTimeDays),
        targetCoverDays: Number(targetCoverDays),
      });
      setDraft(result);
    } catch (error) {
      setDraftError(error instanceof Error ? error.message : "Could not prepare a restock draft.");
    } finally {
      setIsPreparing(false);
    }
  };

  const handleCopyDraft = async () => {
    if (!draft?.draft || draft.recommended_order_quantity === undefined) return;
    const text = [
      draft.draft.title,
      `SKU: ${draft.draft.sku || "Not provided"}`,
      `Suggested quantity: ${draft.recommended_order_quantity}`,
      `Current stock: ${draft.product?.stock_quantity}`,
      `Sales in last 30 days: ${draft.product?.units_sold_last_30d}`,
      draft.basis,
      draft.draft.note,
    ].filter(Boolean).join("\n");
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };
  return (
    <section className="glass-card" style={{ padding: "18px 22px", marginBottom: "24px" }} aria-labelledby="inventory-risk-heading">
      <h2 id="inventory-risk-heading" style={{ margin: "0 0 10px", fontSize: "0.95rem", display: "flex", alignItems: "center", gap: "8px" }}>
        <Boxes size={17} color="var(--accent-teal)" /> Stock risk
        {inventory?.available && <span style={{ marginLeft: "auto", color: "var(--text-secondary)", fontSize: "0.75rem", fontWeight: 500 }}>{inventory.at_risk_count} flagged</span>}
      </h2>
      {!inventory?.available ? (
        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.84rem" }}>
          No current stock quantities are available. Upload a product CSV with <code>stock_quantity</code>; add <code>reorder_point</code> for your own low-stock threshold.
        </p>
      ) : (
        <>
          <p style={{ margin: "0 0 12px", color: "var(--text-secondary)", fontSize: "0.8rem" }}>
            Estimates use the latest 30 days of recorded sales and do not account for supplier lead time.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "10px" }}>
            {inventory.products.slice(0, 6).map((product) => (
              <div key={`${product.sku}-${product.name}`} style={{ border: "1px solid var(--card-border)", borderRadius: "10px", padding: "11px 13px", background: "var(--card-subtle-bg)" }}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                  {product.at_risk && <CircleAlert size={15} color="var(--accent-amber)" aria-label="Low stock" />}
                  <strong style={{ fontSize: "0.83rem", color: "var(--text-primary)" }}>{product.name}</strong>
                </div>
                <p style={{ margin: "7px 0 0", fontSize: "0.77rem", color: "var(--text-secondary)" }}>
                  {product.stock_quantity} in stock · {product.units_sold_last_30d} sold in 30 days
                  {product.estimated_days_of_cover !== null && ` · ~${product.estimated_days_of_cover} days cover`}
                </p>
                {product.at_risk && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ marginTop: "10px", padding: "6px 9px", fontSize: "0.75rem" }}
                    onClick={() => {
                      setSelectedProduct(product);
                      setDraft(null);
                      setDraftError(null);
                      setLeadTimeDays("");
                    }}
                  >
                    <ClipboardList size={14} /> Prepare restock draft
                  </button>
                )}
              </div>
            ))}
          </div>
          {selectedProduct && (
            <div style={{ marginTop: "14px", padding: "14px", border: "1px solid var(--card-border)", borderRadius: "10px", background: "var(--card-subtle-bg)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "flex-start" }}>
                <div>
                  <strong style={{ color: "var(--text-primary)", fontSize: "0.88rem" }}>Restock draft · {selectedProduct.name}</strong>
                  <p style={{ margin: "4px 0 12px", color: "var(--text-secondary)", fontSize: "0.77rem" }}>
                    Enter the supplier lead time. The estimate uses the last 30 days of completed sales and your selected extra cover.
                  </p>
                </div>
                <button type="button" className="btn btn-secondary" onClick={() => { setSelectedProduct(null); setDraft(null); }} aria-label="Close restock draft">×</button>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "end" }}>
                <label style={{ display: "grid", gap: "5px", color: "var(--text-secondary)", fontSize: "0.76rem" }}>
                  Supplier lead time (days)
                  <input className="select-input" type="number" min="0" max="180" step="1" value={leadTimeDays} onChange={(event) => setLeadTimeDays(event.target.value)} placeholder="e.g. 7" style={{ width: "150px" }} />
                </label>
                <label style={{ display: "grid", gap: "5px", color: "var(--text-secondary)", fontSize: "0.76rem" }}>
                  Extra stock cover (days)
                  <input className="select-input" type="number" min="1" max="365" step="1" value={targetCoverDays} onChange={(event) => setTargetCoverDays(event.target.value)} style={{ width: "150px" }} />
                </label>
                <button type="button" className="btn btn-primary" disabled={isPreparing || leadTimeDays === ""} onClick={handlePrepareDraft}>
                  {isPreparing ? "Preparing…" : "Calculate draft"}
                </button>
              </div>
              {draftError && <p role="alert" style={{ color: "var(--accent-rose)", margin: "10px 0 0", fontSize: "0.8rem" }}>{draftError}</p>}
              {draft && (
                <div role="status" style={{ marginTop: "12px", padding: "12px", background: "var(--card-bg)", borderRadius: "8px" }}>
                  {draft.available ? (
                    <>
                      <strong style={{ color: "var(--text-primary)" }}>
                        {draft.recommended_order_quantity === 0
                          ? "No reorder needed for the selected target"
                          : `Suggested order: ${draft.recommended_order_quantity} units`}
                      </strong>
                      <p style={{ margin: "6px 0", color: "var(--text-secondary)", fontSize: "0.78rem" }}>
                        Current stock {draft.product?.stock_quantity} · target stock {draft.target_stock_quantity} · average {draft.average_daily_sales} units/day
                      </p>
                      <p style={{ margin: "6px 0", color: "var(--text-secondary)", fontSize: "0.78rem" }}>{draft.basis}</p>
                      <p style={{ margin: "6px 0 10px", color: "var(--text-secondary)", fontSize: "0.75rem" }}>
                        Draft for human review only. No purchase order has been sent.
                      </p>
                      {draft.recommended_order_quantity !== 0 && (
                        <button type="button" className="btn btn-secondary" onClick={handleCopyDraft} style={{ padding: "6px 9px", fontSize: "0.75rem" }}>
                          {copied ? <Check size={14} /> : <Copy size={14} />}{copied ? "Copied" : "Copy draft"}
                        </button>
                      )}
                    </>
                  ) : <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.8rem" }}>{draft.message}</p>}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
};
