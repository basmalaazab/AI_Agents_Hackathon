export interface KPIMetric {
  current: number;
  previous: number | null;
  absolute_change: number | null;
  percentage_change: number | null;
}

export interface OverviewKPIs {
  period: {
    preset: string;
    current_start: string | null;
    current_end: string | null;
    previous_start: string | null;
    previous_end: string | null;
  };
  kpis: {
    revenue: KPIMetric;
    orders: KPIMetric;
    avg_order_value: KPIMetric;
    active_customers: KPIMetric;
    cancellation_rate: {
      current: number;
      previous: number;
      cancelled_orders: number;
      total_order_attempts: number;
    };
  };
}

export interface RevenueTrendPoint {
  date: string;
  revenue: number;
  orders: number;
  avg_order_value: number;
}

export interface CategoryBreakdown {
  category: string;
  units_sold: number;
  revenue: number;
  order_count: number;
  percentage_of_total: number;
}

export interface PlatformBreakdown {
  platform: string;
  orders: number;
  revenue: number;
}

export interface TopProduct {
  name: string;
  sku: string;
  category: string;
  units_sold: number;
  revenue: number;
  order_count: number;
}

export interface SalesBreakdownData {
  by_category: CategoryBreakdown[];
  by_platform: PlatformBreakdown[];
  top_products: TopProduct[];
}

export interface TopCustomer {
  customer_id: string;
  name: string;
  email: string;
  source_name: string;
  order_count: number;
  lifetime_value: number;
  last_order_date: string | null;
}

export interface CustomerAnalyticsData {
  summary: {
    total_registered_customers: number;
    customers_with_orders: number;
    active_in_period: number;
    new_in_period: number;
    repeat_customer_rate: number;
    churn_at_risk_count: number;
  };
  frequency_cohorts: {
    "1_order": number;
    "2_3_orders": number;
    "4_5_orders": number;
    "6_plus_orders": number;
  };
  top_customers: TopCustomer[];
}

export interface BusinessAlert {
  id: string;
  severity: "danger" | "warning" | "info" | "success";
  title: string;
  message: string;
  metric: string;
  change_pct?: number;
  value?: number;
}
