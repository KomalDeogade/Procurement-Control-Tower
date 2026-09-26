# SCM Procurement Control Tower – Current State Audit

Date: September 26, 2026
Scope: Full codebase inspection (Frontend, Backend, Database, Mock SAP, n8n, AI Services)

---

## 1. System Component Status Summary

| Feature / Module | Audit Status | Key Findings / Current Implementation |
| :--- | :---: | :--- |
| **Frontend Routes & Layout** | **PARTIALLY IMPLEMENTED** | Routes exist in `App.tsx` (`/`, `/requirements`, `/suppliers`, `/rfqs`, `/quotes`, `/approvals`, `/purchase-orders`, `/goods-receipts`, `/inventory`, `/invoices`, `/payments`, `/audit-log`, `/ai`, `/exceptions`, `/reports`, `/demo`, `/supplier/rfq/:rfqId`). All users see the same navigation bar without role-based route filtering. |
| **Backend APIs** | **IMPLEMENTED** | Complete FastAPI REST endpoints in `app/api/` covering requirements, suppliers, RFQs, quotes, approvals, POs, inventory, GRN, invoices, payments, dashboard, audit, exceptions, reports, demo, and AI. |
| **Database Schema** | **PARTIALLY IMPLEMENTED** | Models exist in `app/models/` for `User`, `Requirement`, `Supplier`, `RFQ`, `SupplierQuote`, `Approval`, `PurchaseOrder`, `GoodsReceipt`, `InventoryItem`, `Invoice`, `Payment`, `AuditLog`, `Notification`. Missing `STORE_USER` and `SUPPLIER` in `UserRole` enum; missing `supplier_id` link on `User` model. |
| **Role & Authentication** | **PARTIALLY IMPLEMENTED** | JWT authentication implemented (`security.py`, `auth_service.py`). Roles `SCM_USER`, `PROCUREMENT_MANAGER`, `FINANCE_USER`, `ADMIN` exist in enum. However, backend routes fall back to default user if no header is present, and no route enforcement (`HTTP 403 Forbidden`) exists per role. No supplier data isolation. |
| **Supplier Portal** | **PARTIALLY IMPLEMENTED** | Route `/supplier/rfq/:rfqId` exists in `SupplierPortalPage.tsx`. Uses numeric RFQ ID instead of a secure tokenized link `/supplier/rfq/<token>`. No backend validation preventing a supplier from altering IDs or seeing other suppliers' data. |
| **Quote Comparison & Scoring** | **IMPLEMENTED** | `scoring_service.py` provides deterministic weighted scoring (Price, Quality, Delivery, Performance, Terms, Availability, Risk). Needs alignment to exact prompt weights (Price 30%, Delivery 20%, Quality 15%, Performance 15%, Terms 10%, Availability 5%, Risk 5%) and natural-language AI explanation. |
| **Inventory & Stock Risk** | **PARTIALLY IMPLEMENTED** | Stock levels tracked in `InventoryItem`. Standard safety stock checks exist. Missing deterministic calculation of available stock, coverage days, projected stockout date, and reorder quantity explanation. |
| **Invoice & 3-Way Match** | **IMPLEMENTED** | `three_way_match.py` matches PO quantity/price, GRN quantity, and Invoice quantity/price. Sets status to `MATCHED` or `DISCREPANCY`. Needs backend override workflow with audit logging. |
| **Payment Logic & Terms** | **PARTIALLY IMPLEMENTED** | `payment_service.py` handles mock payment execution. `Invoice.due_date` calculation is basic. Missing configurable payment terms (15, 30, 45, 60 days) and prepaid supplier balance tracking workflow. |
| **Audit Log** | **IMPLEMENTED** | `audit_service.py` logs actor, action, entity_type, entity_id, old_value, new_value. Needs correlation ID / request ID tracking across the entire workflow. |
| **Demo Mode** | **IMPLEMENTED** | `demo.py` and `DemoPage.tsx` run end-to-end simulation. Needs separate "Run Exception Demo" (supplier delay, invoice mismatch, stockout risk, payment due, advance payment risk). |
| **AI Features & Daily Brief** | **PARTIALLY IMPLEMENTED** | `ai_service.py` provides provider-agnostic Gemini/OpenAI wrapper with fallback. AI Daily Brief and AI Negotiation Drafter exist. PDF quotation document extraction to structured JSON needs implementation with Pydantic validation. |
| **Automation / n8n Integration** | **STATIC/SEEDED** | `n8n/.gitkeep` placeholder exists. No live n8n workflow JSON exported or webhook triggers wired to FastAPI endpoints yet. |
| **Mock SAP Implementation** | **IMPLEMENTED** | Separate FastAPI service in `mock-sap/` (Port 8001) connected via abstract `SAPAdapter` interface (`MockSAPAdapter`). Returns simulated SAP PO numbers (e.g., `450001001`). |

---

## 2. Detailed Technical Inventory

### Frontend Routes (`frontend/src/App.tsx`)
- `/login` - Login Page
- `/supplier/rfq/:rfqId` - Supplier Portal (Unsecured RFQ ID route)
- `/` - Main Dashboard
- `/requirements` - Procurement Requisitions
- `/suppliers` - Supplier Directory
- `/rfqs` - RFQs Manager
- `/quotes` - Quote Comparison & Scoring
- `/approvals` - Approval Workflows
- `/purchase-orders` - Purchase Orders & SAP Sync
- `/goods-receipts` - Goods Receipt Notes (GRN)
- `/inventory` - Stock Management
- `/invoices` - Invoices & 3-Way Match
- `/payments` - Payment Processing
- `/audit-log` - Immutable Audit Trail
- `/ai` - AI Features Hub
- `/exceptions` - Exceptions & Monitoring
- `/reports` - Reports & Analytics
- `/demo` - Demo Mode Control Panel

### Backend Routers (`backend/app/api/`)
- `auth.py`, `requirements.py`, `suppliers.py`, `rfqs.py`, `quotes.py`, `approvals.py`, `purchase_orders.py`, `inventory.py`, `goods_receipts.py`, `invoices.py`, `payments.py`, `dashboard.py`, `audit.py`, `ai_features.py`, `exceptions_monitor.py`, `reports.py`, `demo.py`

### Backend Services (`backend/app/services/`)
- `ai_service.py` - AI provider interface & daily brief
- `audit_service.py` - Audit logger
- `auth_service.py` - Password hashing & JWT
- `inventory_service.py` - Stock updates on GRN
- `mock_payment_service.py` - Payment UTR generator
- `payment_service.py` - Payment categorization
- `scoring_service.py` - Weighted supplier scoring
- `three_way_match.py` - 3-Way match verifier
