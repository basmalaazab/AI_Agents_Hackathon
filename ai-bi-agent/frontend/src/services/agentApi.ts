/**
 * Person 3: AI Business Intelligence Agent API Client.
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

const AGENT_BASE_URL = `${API_V1}/agent`;

export async function askAIAgent(
  query: string,
  dateRange: string = "30d",
  sourceName?: string,
  conversationHistory?: { role: string; content: string }[],
  includeSql: boolean = true
): Promise<AgentQueryResponse> {
  const res = await fetch(`${AGENT_BASE_URL}/query`, {
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

export async function fetchRecommendations(
  dateRange: string = "30d",
  sourceName?: string,
  categoryFocus?: string
): Promise<RecommendationsResponse> {
  const res = await fetch(`${AGENT_BASE_URL}/recommendations`, {
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
  const res = await fetch(`${AGENT_BASE_URL}/diagnose`, {
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
  const res = await fetch(`${AGENT_BASE_URL}/sql`, {
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

  const res = await fetch(`${AGENT_BASE_URL}/suggestions?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch prompt suggestions");
  return res.json();
}

export async function fetchAgentCapabilities(): Promise<AgentCapabilities> {
  const res = await fetch(`${AGENT_BASE_URL}/capabilities`);
  if (!res.ok) throw new Error("Failed to fetch agent capabilities");
  return res.json();
}
