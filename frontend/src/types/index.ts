/* ── Types ──────────────────────────────────────────────── */

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type UserRole = 'SUPPLIER' | 'SCM_USER' | 'PROCUREMENT_MANAGER' | 'STORE_USER' | 'FINANCE_USER' | 'ADMIN';

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface Requirement {
  id: number;
  display_id: string | null;
  material_code: string;
  material_name: string;
  description: string | null;
  quantity: number;
  unit: string;
  plant: string | null;
  required_by_date: string | null;
  budget: number | null;
  currency: string;
  priority: RequirementPriority;
  status: RequirementStatus;
  created_by: number | null;
  created_at: string;
}

export type RequirementStatus =
  | 'DRAFT' | 'SUBMITTED' | 'RFQ_IN_PROGRESS' | 'QUOTES_RECEIVED'
  | 'UNDER_REVIEW' | 'APPROVAL_PENDING' | 'APPROVED' | 'REJECTED'
  | 'PO_CREATED' | 'COMPLETED' | 'CANCELLED';

export type RequirementPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Supplier {
  id: number;
  supplier_code: string;
  company_name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  category: string | null;
  location: string | null;
  quality_score: number;
  delivery_score: number;
  risk_score: number;
  payment_terms: string | null;
  approval_status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_requirements: number;
  active_suppliers: number;
  open_purchase_orders: number;
  pending_approvals: number;
  total_spend: number;
  pending_invoices: number;
  overdue_payments: number;
}
