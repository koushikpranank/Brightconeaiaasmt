import type {
  ActionItem,
  Alert,
  AnalyticsSummary,
  ApprovalRequest,
  DashboardSummary,
  DisruptionCase,
  InventoryItem,
  LogisticsUpdate,
  PurchaseOrder,
  Supplier,
  TraceEntry,
} from "../types";

// In dev, Vite proxies "/api" to the local backend (see vite.config.ts). In production
// (e.g. frontend on Vercel, backend on Render) set VITE_API_BASE to the backend's full URL.
const BASE = `${import.meta.env.VITE_API_BASE ?? ""}/api`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  suppliers: () => request<Supplier[]>("/suppliers"),
  inventory: () => request<InventoryItem[]>("/inventory"),
  purchaseOrders: () => request<PurchaseOrder[]>("/purchase-orders"),
  shipments: () => request<LogisticsUpdate[]>("/shipments"),
  cases: () => request<DisruptionCase[]>("/disruptions/cases"),
  case: (caseNumber: string) => request<DisruptionCase>(`/disruptions/cases/${caseNumber}`),
  alerts: () => request<Alert[]>("/alerts"),
  actions: () => request<ActionItem[]>("/actions"),
  updateAction: (id: number, status: string) =>
    request<ActionItem>(`/actions/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
  approvals: () => request<ApprovalRequest[]>("/approvals"),
  decideApproval: (id: number, approver: string, decision: "approved" | "rejected", notes?: string) =>
    request<ApprovalRequest>(`/approvals/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ approver, decision, notes }),
    }),
  dashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
  runMonitoring: () => request<{ checked_at: string; cases_processed: string[] }>("/monitoring/run", { method: "POST" }),
  simulateDelay: (po_number: string, material: string, supplier_code: string, delay_days: number, reason?: string) =>
    request("/monitoring/simulate-delay", {
      method: "POST",
      body: JSON.stringify({ po_number, material, supplier_code, delay_days, reason }),
    }),
  simulateRestore: (po_number: string) => request(`/monitoring/simulate-restore/${po_number}`, { method: "POST" }),
  simulateLeadTimeIncrease: (supplier_code: string, new_lead_time_days: number) =>
    request("/monitoring/simulate-lead-time-increase", {
      method: "POST",
      body: JSON.stringify({ supplier_code, new_lead_time_days }),
    }),
  simulateLeadTimeRestore: (supplier_code: string) =>
    request(`/monitoring/simulate-lead-time-restore/${supplier_code}`, { method: "POST" }),
  reportPdfUrl: (caseNumber: string) => `${BASE}/reports/${caseNumber}/pdf`,
  analyticsSummary: () => request<AnalyticsSummary>("/analytics/summary"),
  caseTrace: (caseNumber: string) => request<TraceEntry[]>(`/disruptions/cases/${caseNumber}/trace`),
};
