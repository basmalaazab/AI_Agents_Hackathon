/**
 * AI Business Analyst – API client for the agent endpoints.
 */
import type {
  AgentQueryResponse,
  RecommendationsResponse,
  AnomalyDiagnosis,
  SQLResults,
  PromptSuggestion,
  AgentCapabilities,
} from "../types/agent";
import { API_V1 } from "./config";
import { authenticatedFetch } from "./auth";

const AGENT_BASE_URL = `${API_V1}/agent`;

export interface InventoryReorderDraft {
  available: boolean;
  status?: string;
  product?: {
    name: string;
    sku: string | null;
    stock_quantity: number;
    units_sold_last_30d: number;
    estimated_days_of_cover: number | null;
  };
  supplier_lead_time_days?: number;
  target_cover_days?: number;
  average_daily_sales?: number;
  target_stock_quantity?: number;
  recommended_order_quantity?: number;
  basis?: string;
  draft?: {
    title: string;
    sku: string | null;
    quantity: number;
    status: string;
    note: string;
  };
  message?: string;
}

export async function prepareInventoryReorderDraft(input: {
  productName: string;
  productSku: string | null;
  sourceName: string;
  supplierLeadTimeDays: number;
  targetCoverDays: number;
}): Promise<InventoryReorderDraft> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/inventory-reorder-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_name: input.productName,
      product_sku: input.productSku,
      source_name: input.sourceName,
      supplier_lead_time_days: input.supplierLeadTimeDays,
      target_cover_days: input.targetCoverDays,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Could not prepare a restock draft");
  }
  return res.json();
}

export async function askAIAgent(
  query: string,
  dateRange: string = "30d",
  sourceName?: string,
  conversationHistory?: { role: string; content: string }[],
  includeSql: boolean = true
): Promise<AgentQueryResponse> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      date_range: dateRange,
      source_name: sourceName || null,
      conversation_history: conversationHistory || null,
      include_sql: includeSql,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to query AI Agent");
  }
  return res.json();
}

export async function streamAIAgent(
  query: string,
  dateRange: string = "30d",
  sourceName?: string,
  conversationHistory?: { role: string; content: string }[],
  onChunk?: (token: string, modelUsed?: string) => void,
  onComplete?: (finalResponse: AgentQueryResponse) => void
): Promise<AgentQueryResponse> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      date_range: dateRange,
      source_name: sourceName || null,
      conversation_history: conversationHistory || null,
      include_sql: true,
    }),
  });

  if (!res.ok) {
    return askAIAgent(query, dateRange, sourceName, conversationHistory, true);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    return askAIAgent(query, dateRange, sourceName, conversationHistory, true);
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: AgentQueryResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const block of lines) {
      const match = block.match(/^data:\s*(.+)$/m);
      if (match) {
        try {
          const payload = JSON.parse(match[1]);
          if (payload.chunk && onChunk) {
            onChunk(payload.chunk, payload.model_used);
          }
          if (payload.done && payload.full_result) {
            finalResult = payload.full_result;
            if (onComplete) onComplete(payload.full_result);
          }
        } catch {
          // ignore
        }
      }
    }
  }

  if (finalResult) return finalResult;
  return askAIAgent(query, dateRange, sourceName, conversationHistory, true);
}

export async function fetchRecommendations(
  dateRange: string = "30d",
  sourceName?: string,
  categoryFocus?: string
): Promise<RecommendationsResponse> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      date_range: dateRange,
      source_name: sourceName || null,
      category_focus: categoryFocus || null,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to fetch strategic recommendations");
  }
  return res.json();
}

export async function fetchDiagnoses(
  dateRange: string = "30d",
  sourceName?: string,
  alertId?: string
): Promise<AnomalyDiagnosis[]> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      date_range: dateRange,
      source_name: sourceName || null,
      alert_id: alertId || null,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to fetch anomaly diagnosis");
  }
  return res.json();
}

export async function executeSafeSQL(
  query: string,
  maxRows: number = 50
): Promise<SQLResults> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/sql`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, max_rows: maxRows }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "SQL execution error");
  }
  return res.json();
}

export async function fetchPromptSuggestions(
  dateRange: string = "30d",
  sourceName?: string
): Promise<PromptSuggestion[]> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);

  const res = await authenticatedFetch(`${AGENT_BASE_URL}/suggestions?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch prompt suggestions");
  return res.json();
}

export async function fetchAgentCapabilities(): Promise<AgentCapabilities> {
  const res = await authenticatedFetch(`${AGENT_BASE_URL}/capabilities`);
  if (!res.ok) throw new Error("Failed to fetch agent capabilities");
  return res.json();
}
