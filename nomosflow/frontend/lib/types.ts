export interface Partner {
  id: string;
  name: string;
  slug: string;
  device_type: string;
  brand_color: string;
  logo_url: string | null;
  customer_count: number;
  created_at: string;
}

export interface Customer {
  id: string;
  partner_id: string;
  name: string;
  email: string;
  phone: string | null;
  tariff_type: string;
  device_type: string;
  monthly_kwh: number | null;
  annual_saving_eur: number | null;
  salary_day: number | null;
  contract_start: string;
  contract_status: string;
  city: string | null;
  created_at: string;
}

export interface CustomerFullProfile extends Customer {
  partner_name: string | null;
  latest_churn_score: number | null;
  latest_risk_level: string | null;
  failed_payments_count: number;
  total_payments_count: number;
}

export interface Payment {
  id: string;
  customer_id: string;
  amount_eur: number;
  period_month: string;
  due_date: string;
  paid_at: string | null;
  status: string;
  failure_reason: string | null;
  failure_classified_by: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_date: string | null;
  created_at: string;
  customer_name?: string;
  partner_name?: string;
  device_type?: string;
}

export interface DunningAction {
  id: string;
  payment_id: string;
  customer_id: string;
  action_type: string;
  ai_generated_message: string | null;
  ai_failure_reason: string | null;
  ai_confidence: number | null;
  retry_scheduled_for: string | null;
  triggered_by: string;
  outcome: string | null;
  executed_at: string;
}

export interface ChurnScore {
  id: string;
  customer_id: string;
  score: number;
  risk_level: string;
  reasoning: string | null;
  factors: Record<string, unknown> | null;
  action_suggested: string | null;
  scored_at: string;
  customer_name?: string;
  partner_name?: string;
  device_type?: string;
  contract_status?: string;
}

export interface DashboardSummary {
  total_customers: number;
  failed_payments: number;
  at_risk_customers: number;
  revenue_at_risk_eur: number;
}

export interface RetentionMessage {
  subject: string;
  body: string;
  tone: string;
  highlight_phrase: string;
}
