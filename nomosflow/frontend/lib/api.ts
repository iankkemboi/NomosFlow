import type {
  Partner, Customer, CustomerFullProfile, Payment,
  DunningAction, ChurnScore, DashboardSummary, RetentionMessage,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response, label: string): Promise<T> {
  if (res.ok) return res.json();
  let body: unknown;
  try { body = await res.json(); } catch { /* non-JSON error body */ }
  const message =
    (body as { message?: string })?.message ??
    (body as { detail?: string })?.detail ??
    `${label} → ${res.status}`;
  throw new ApiError(res.status, message, body);
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  return handleResponse<T>(res, `GET ${path}`);
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res, `POST ${path}`);
}

// Partners
export const getPartners = () => get<Partner[]>("/api/partners");
export const getPartner  = (id: string) => get<Partner>(`/api/partners/${id}`);

// Customers
export const getCustomers = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return get<Customer[]>(`/api/customers${qs}`);
};
export const getCustomerFullProfile = (id: string) =>
  get<CustomerFullProfile>(`/api/customers/${id}/full-profile`);

// Payments
export const getPayments = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return get<Payment[]>(`/api/payments${qs}`);
};
export const getCustomerPayments = (customerId: string) =>
  get<Payment[]>(`/api/payments/customer/${customerId}`);

// Dunning
export const getDunningQueue    = () => get<unknown[]>("/api/dunning/queue");
export const getDunningTimeline = (customerId: string) =>
  get<DunningAction[]>(`/api/dunning/timeline/${customerId}`);
export const runDunningCycle    = (partnerId?: string, limit = 5) => {
  const params = new URLSearchParams();
  if (partnerId) params.set("partner_id", partnerId);
  params.set("limit", String(limit));
  return post<{ status: string; processed: number; actions: { type: string; by?: string; reason?: string; confidence?: number; date?: string }[]; errors: unknown[]; queue_remaining: number }>(`/api/dunning/run-cycle?${params.toString()}`);
};

// Churn
export const getChurnScores = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return get<ChurnScore[]>(`/api/churn/scores${qs}`);
};
export const scoreAllCustomers = (useAi = false) =>
  post<{ status: string; scored: number; errors: unknown[] }>(`/api/churn/score-all?use_ai=${useAi}`);

// AI
export const getDashboardSummary    = () => get<DashboardSummary>("/api/ai/dashboard-summary");
export const getRetentionMessage    = (customerId: string) =>
  post<RetentionMessage>("/api/ai/retention-message", { customer_id: customerId });
