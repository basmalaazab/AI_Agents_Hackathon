import type {
  OverviewKPIs,
  RevenueTrendPoint,
  SalesBreakdownData,
  CustomerAnalyticsData,
  BusinessAlert,
} from "../types/analytics";


const API_BASE_URL = "http://localhost:8000/api/v1/analytics";

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
