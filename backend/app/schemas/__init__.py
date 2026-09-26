"""Pydantic schemas for all domain entities."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ═══════════════════════════════════════════════════════════════
#  Auth
# ═══════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "SCM_USER"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Requirement
# ═══════════════════════════════════════════════════════════════
class RequirementCreate(BaseModel):
    material_code: str
    material_name: str
    description: Optional[str] = None
    quantity: float
    unit: str
    plant: Optional[str] = None
    required_by_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: str = "INR"
    priority: str = "MEDIUM"

class RequirementUpdate(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    plant: Optional[str] = None
    required_by_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class RequirementResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    material_code: str
    material_name: str
    description: Optional[str] = None
    quantity: float
    unit: str
    plant: Optional[str] = None
    required_by_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: str
    priority: str
    status: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Supplier
# ═══════════════════════════════════════════════════════════════
class SupplierCreate(BaseModel):
    supplier_code: Optional[str] = None
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    registration_number: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quality_score: float = 0.0
    delivery_score: float = 0.0
    risk_score: float = 0.0
    payment_terms: Optional[str] = None
    approval_status: str = "PENDING"

class SupplierUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quality_score: Optional[float] = None
    delivery_score: Optional[float] = None
    risk_score: Optional[float] = None
    payment_terms: Optional[str] = None
    approval_status: Optional[str] = None

class SupplierResponse(BaseModel):
    id: int
    supplier_code: Optional[str] = None
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    registration_number: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quality_score: float
    delivery_score: float
    risk_score: float
    payment_terms: Optional[str] = None
    approval_status: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  RFQ
# ═══════════════════════════════════════════════════════════════
class RFQCreate(BaseModel):
    requirement_id: int
    supplier_id: int
    response_deadline: Optional[datetime] = None
    notes: Optional[str] = None

class RFQResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    requirement_id: int
    supplier_id: int
    status: str
    response_deadline: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Supplier Quote
# ═══════════════════════════════════════════════════════════════
class QuoteCreate(BaseModel):
    requirement_id: int
    supplier_id: int
    unit_price: float
    quantity: float
    tax: float = 0.0
    freight: float = 0.0
    total_price: float
    availability: Optional[str] = None
    lead_time_days: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    warranty: Optional[str] = None
    service_details: Optional[str] = None
    advantages: Optional[str] = None
    limitations: Optional[str] = None

class QuoteResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    requirement_id: int
    supplier_id: int
    unit_price: float
    quantity: float
    tax: float
    freight: float
    total_price: float
    availability: Optional[str] = None
    lead_time_days: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    warranty: Optional[str] = None
    service_details: Optional[str] = None
    advantages: Optional[str] = None
    limitations: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Approval
# ═══════════════════════════════════════════════════════════════
class ApprovalCreate(BaseModel):
    entity_type: str
    entity_id: int
    approver_id: int
    approval_level: int = 1
    comments: Optional[str] = None

class ApprovalAction(BaseModel):
    status: str  # APPROVED, REJECTED, REVISION_REQUIRED
    comments: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    entity_type: str
    entity_id: int
    approver_id: int
    approval_level: int
    status: str
    comments: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Purchase Order
# ═══════════════════════════════════════════════════════════════
class POCreate(BaseModel):
    requirement_id: int
    supplier_id: int
    quote_id: Optional[int] = None
    material_code: str
    material_name: Optional[str] = None
    quantity: float
    unit_price: float
    total_amount: float
    currency: str = "INR"
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None

class POResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    requirement_id: int
    supplier_id: int
    quote_id: Optional[int] = None
    sap_po_number: Optional[str] = None
    material_code: str
    material_name: Optional[str] = None
    quantity: float
    unit_price: float
    total_amount: float
    currency: str
    delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Goods Receipt
# ═══════════════════════════════════════════════════════════════
class GRNCreate(BaseModel):
    po_id: int
    received_quantity: float
    quality_status: str = "PENDING_INSPECTION"
    inspector: Optional[str] = None
    remarks: Optional[str] = None

class GRNResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    po_id: int
    received_quantity: float
    received_date: Optional[datetime] = None
    quality_status: str
    inspector: Optional[str] = None
    remarks: Optional[str] = None
    sap_grn_number: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Inventory
# ═══════════════════════════════════════════════════════════════
class InventoryResponse(BaseModel):
    id: int
    material_code: str
    material_name: str
    quantity_on_hand: float
    unit: str
    plant: Optional[str] = None
    warehouse: Optional[str] = None
    reorder_level: float
    safety_stock: float
    minimum_stock: float
    average_daily_consumption: float
    lead_time_days: int
    reserved_quantity: float
    last_updated: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Invoice
# ═══════════════════════════════════════════════════════════════
class InvoiceCreate(BaseModel):
    po_id: int
    supplier_id: int
    invoice_amount: float
    tax_amount: float = 0.0
    total_amount: float
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    po_id: int
    supplier_id: int
    invoice_amount: float
    tax_amount: float
    total_amount: float
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: str
    sap_invoice_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Payment
# ═══════════════════════════════════════════════════════════════
class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str = "BANK_TRANSFER"

class PaymentResponse(BaseModel):
    id: int
    display_id: Optional[str] = None
    invoice_id: int
    amount: float
    payment_date: Optional[datetime] = None
    payment_method: str
    status: str
    reference_number: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
#  Audit Log
# ═══════════════════════════════════════════════════════════════
class AuditLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: Optional[datetime] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    model_config = {"from_attributes": True}
