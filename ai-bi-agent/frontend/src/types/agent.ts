/**
 * Person 3: AI Business Intelligence Agent TypeScript Definitions.
 */

export interface MetricsSnapshot {
  revenue: number;
  orders: number;
  aov: number;
  cancellation_rate: number;
  repeat_customer_rate: number | null;
  churn_risk_count: number | null;
}

export interface SQLResults {
  success: boolean;
  query: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  is_limited?: boolean;
  error?: string;
}

export interface AgentQueryResponse {
  query: string;
  intent: string;
  model_used: string;
  generated_at: string;
  answer: string;
  executed_sql?: string | null;
  sql_results?: SQLResults | null;
  metrics_snapshot: MetricsSnapshot;
  suggested_followups: string[];
}

export interface StrategicRecommendation {
  id: string;
  title: string;
  category: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  expected_impact: string;
  implementation_effort: "LOW" | "MEDIUM" | "HIGH";
  target_metric: string;
  data_justification: string;
  action_steps: string[];
}

export interface RecommendationsResponse {
  generated_at: string;
  period: {
    label: string;
    start: string | null;
    end: string | null;
  };
  total_recommendations: number;
  high_priority_count: number;
  executive_summary: string;
  key_risks: string[];
  quick_wins: string[];
  recommendations: StrategicRecommendation[];
}

export interface AnomalyDiagnosis {
  id: string;
  title: string;
  severity: "danger" | "warning" | "info";
  metric: string;
  current_value: number;
  baseline_value: number | null;
  change_pct: number | null;
  summary: string;
  root_causes: string[];
  contributing_factors: string[];
  evidence: Record<string, any>;
  mitigation_actions: string[];
}

export interface PromptSuggestion {
  category: string;
  prompt: string;
  icon: string;
}

export interface AgentCapabilities {
  service: string;
  version: string;
  description: string;
  supported_models: string[];
  database_schema: Record<string, any>;
  security_guardrails: {
    read_only: boolean;
    allowed_statements: string[];
    max_rows_default: number;
    disallowed_keywords: string[];
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  intent?: string;
  model_used?: string;
  executed_sql?: string | null;
  sql_results?: SQLResults | null;
  metrics_snapshot?: MetricsSnapshot;
  suggested_followups?: string[];
}
