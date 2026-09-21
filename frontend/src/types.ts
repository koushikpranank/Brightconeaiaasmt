export interface Supplier {
  id: number;
  supplier_code: string;
  name: string;
  material: string;
  lead_time_days: number | null;
  baseline_lead_time_days: number | null;
  price_per_unit: number | null;
  currency: string;
  available_quantity: number | null;
  capacity_units_per_month: number | null;
  capacity_notes: string | null;
  approved: boolean;
  is_primary: boolean;
  status: string;
}

export interface InventoryItem {
  id: number;
  material: string;
  unit: string;
  current_quantity: number;
  daily_consumption: number;
  required_quantity: number | null;
  reorder_point_days: number;
  snapshot_at: string | null;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  material: string;
  supplier_code: string;
  quantity: number;
  original_delivery_date: string;
  revised_delivery_date: string | null;
  status: string;
}

export interface LogisticsUpdate {
  id: number;
  po_number: string;
  carrier: string | null;
  status: string;
  location: string | null;
  eta: string | null;
  delay_days: number;
  source: string;
  reported_at: string;
}

export interface InventoryAnalysis {
  material?: string;
  current_quantity?: number | null;
  daily_consumption?: number | null;
  snapshot_at?: string | null;
  coverage_days?: number | null;
  projected_stockout_date?: string | null;
  stockout_calculable?: boolean;
  reorder_required?: boolean;
  notes?: string[];
  narrative?: string;
}

export interface ImpactAssessment {
  affected_purchase_orders?: string[];
  affected_production_orders?: string[];
  affected_customers?: string[];
  estimated_delay_days?: number;
  mitigation_window_days?: number | null;
  severity?: string;
  summary?: string;
}

export interface SupplierOption {
  supplier_code: string;
  name: string;
  lead_time_days: number | null;
  price_per_unit: number | null;
  available_quantity: number | null;
  capacity_units_per_month: number | null;
  meets_required_quantity: boolean | null;
  meets_capacity: boolean | null;
  approved: boolean;
  data_confidence: "confirmed" | "requires_verification";
}

export interface Mitigation {
  options?: SupplierOption[];
  recommended_actions?: string[];
  requires_human_approval?: boolean;
  verification_needed?: string[];
  narrative?: string;
  required_quantity?: number | null;
}

export interface Review {
  approved?: boolean;
  issues?: string[];
  revision_target?: string | null;
}

export interface DisruptionCase {
  id: number;
  case_number: string;
  status: string;
  material: string;
  disruption_type: string;
  source: string;
  description: string;
  detected_at: string;
  original_delivery_date: string | null;
  revised_delivery_date: string | null;
  inventory_analysis: InventoryAnalysis;
  impact: ImpactAssessment;
  supplier_options: SupplierOption[];
  mitigation: Mitigation;
  review: Review;
  revision_count: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: number;
  dedup_key: string;
  case_id: number;
  disruption_type: string;
  material: string;
  source: string;
  expected_impact: string;
  recommended_action: string;
  responsible_team: string;
  status: string;
  occurrence_count: number;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRequest {
  id: number;
  case_id: number;
  action_type: string;
  description: string;
  estimated_cost: number | null;
  status: string;
  requested_at: string;
  decided_by: string | null;
  decided_at: string | null;
  notes: string | null;
}

export interface ActionItem {
  id: number;
  case_id: number;
  description: string;
  responsible_team: string;
  status: string;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  active_disruptions: number;
  delayed_shipments: number;
  at_risk_materials: { material: string; coverage_days: number }[];
  at_risk_suppliers: string[];
  open_alerts: number;
  pending_approvals: number;
  open_action_items: number;
  severity_breakdown: Record<string, number>;
}

export interface AnalyticsSummary {
  disruption_frequency_by_material: { material: string; count: number }[];
  severity_distribution: { severity: string; count: number }[];
  disruption_type_breakdown: { disruption_type: string; count: number }[];
  avg_mitigation_window_by_severity: { severity: string; avg_mitigation_window_days: number }[];
  alerts_by_team: { team: string; total_alerts: number; open_alerts: number }[];
  cases_per_day: { date: string; count: number }[];
  reviewer_revision_rate: { total_cases: number; cases_revised: number; revision_rate_pct: number };
  total_cases: number;
  total_alerts: number;
}

export interface TraceEntry {
  agent_name: string;
  input_summary: string;
  output_summary: string;
  evidence: Record<string, unknown>;
  created_at: string;
}
