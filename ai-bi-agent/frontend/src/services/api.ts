import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "../types/analytics";
import { API_V1 } from "./config";

const API_BASE_URL = `${API_V1}/analytics`;

export interface DataSourceInfo {
  id: string;
  name: string;
  source_type: string;
  description: string | null;
  is_active: boolean;
}

export interface PipelineSummary {
  total_runs: number;
  total_quality_errors: number;
  total_customers: number;
  total_orders: number;
  total_products: number;
}

export interface IngestionRunResult {
  id: string;
  status: string;
  records_fetched: number;
  records_valid: number;
  records_invalid: number;
  records_inserted: number;
  records_duplicate: number;
  error_message: string | null;
}

export async function fetchOverviewKPIs(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<OverviewKPIs> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/overview?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch overview KPIs");
  return res.json();
}

export async function fetchRevenueTrends(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<RevenueTrendPoint[]> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/revenue-trends?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch revenue trends");
  return res.json();
}

export async function fetchSalesBreakdown(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<SalesBreakdownData> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/sales-breakdown?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch sales breakdown");
  return res.json();
}

export async function fetchCustomerAnalytics(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<CustomerAnalyticsData> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/customers?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch customer analytics");
  return res.json();
}

export async function fetchBusinessAlerts(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<BusinessAlert[]> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/alerts?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch business alerts");
  return res.json();
}

export async function fetchAIContext(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): Promise<any> {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const res = await fetch(`${API_BASE_URL}/ai-context?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch AI agent context");
  return res.json();
}

export function getExportCSVUrl(
  dateRange: string = "30d",
  sourceName?: string,
  startDate?: string,
  endDate?: string
): string {
  const params = new URLSearchParams({ date_range: dateRange });
  if (sourceName) params.append("source_name", sourceName);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  return `${API_BASE_URL}/export/csv?${params.toString()}`;
}

export async function fetchDataSources(): Promise<DataSourceInfo[]> {
  const res = await fetch(`${API_V1}/sources`);
  if (!res.ok) throw new Error("Failed to fetch data sources");
  return res.json();
}

export async function fetchPipelineSummary(): Promise<PipelineSummary> {
  const res = await fetch(`${API_V1}/pipelines/summary`);
  if (!res.ok) throw new Error("Failed to fetch pipeline summary");
  return res.json();
}

export async function triggerPipeline(
  sourceId: string,
  recordType: "customer" | "product" | "order"
): Promise<IngestionRunResult> {
  const res = await fetch(`${API_V1}/pipelines/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: sourceId, record_type: recordType }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to trigger pipeline");
  }
  return res.json();
}

export async function uploadCsvFile(
  file: File,
  recordType: "customer" | "product" | "order",
  sourceName: string
): Promise<IngestionRunResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("record_type", recordType);
  form.append("source_name", sourceName);

  const res = await fetch(`${API_V1}/upload/csv`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    const detail = errData.detail;
    throw new Error(
      typeof detail === "string" ? detail : "Failed to upload CSV"
    );
  }
  return res.json();
}
