# SCM Procurement Control Tower – Functional Verification Report

Date: September 26, 2026
Audit Scope: Codebase inspection and functional verification across all 20 core workflow features.

---

## 1. Functional Verification Matrix

| # | Feature / Capability | Classification | Verification Findings & Technical Details |
| :-: | :--- | :---: | :--- |
| 1 | **Requirement Creation** | **LIVE** | Fully operational via `POST /api/requirements/` endpoint and frontend `RequirementsPage.tsx`. Generates auto-incrementing `REQ-XXXX` ID, validates fields, and records initial `DRAFT` status with audit trail. |
| 2 | **Supplier Isolation** | **LIVE** | Backend authorization enforces object-level data isolation via `supplier_id` on `User` model (`dependencies.py` + `test_rbac_authorization.py`). A supplier cannot query or view other suppliers' quotes, POs, or internal budgets. |
| 3 | **Supplier RFQ Portal** | **LIVE** | Tokenized secure access via `GET /api/rfqs/token/{token}` and frontend route `/supplier/rfq/:token`. Exposes only assigned RFQ details without disclosing other suppliers. |
| 4 | **Quote Submission** | **LIVE** | Endpoint `POST /api/quotes/` stores supplier responses directly in PostgreSQL/SQLite database with status `SUBMITTED`, triggering audit events. |
| 5 | **Dynamic Supplier Scoring** | **LIVE** | `scoring_service.py` computes deterministic weighted scores (Price 30%, Delivery 20%, Quality 15%, Performance 15%, Payment Terms 10%, Availability 5%, Risk 5%). Returns breakdown and reason codes without LLM math. |
| 6 | **Approval State Transition** | **LIVE** | `approvals.py` manages multi-level managerial and finance approvals. Transition from `PENDING` to `APPROVED` or `REJECTED` updates requirement/PO state and records approval comments. |
| 7 | **PO Creation** | **LIVE** | Endpoint `POST /api/purchase-orders/` converts approved quotes/requirements into Purchase Orders (`PO-XXXX`), computing tax and total amounts. |
| 8 | **SAPAdapter Call** | **LIVE** | `app/integrations/sap_adapter.py` exposes abstract `SAPAdapter` interface. Calls `MockSAPAdapter` during PO creation. |
| 9 | **Mock SAP HTTP Request/Response** | **LIVE** | Dedicated FastAPI microservice (`mock-sap/` on Port 8001). `MockSAPAdapter` sends HTTP POST `/sap/purchase-orders` and receives simulated SAP PO numbers (e.g., `450001001`) with HTTP 201/200 response logging. |
| 10 | **GRN Creation** | **LIVE** | `goods_receipts.py` logs physical receiving, inspector details, and quality status (`PASSED`/`FAILED`), issuing unique GRN number (`GRN-XXXX`). |
| 11 | **Inventory Update** | **LIVE** | `inventory_service.py` automatically increments `quantity_on_hand` upon GRN creation and logs an `inventory_transactions` record. |
| 12 | **Inventory Risk Calculation** | **LIVE** | Computes available stock (`stock - reserved`), stock coverage days (`avail / daily_consumption`), projected stockout date, and risk status (`NORMAL`, `LOW`, `CRITICAL`, `STOCKOUT_RISK`). |
| 13 | **Invoice Creation** | **LIVE** | `invoices.py` logs supplier invoices linked to PO ID, calculating tax and due date based on payment terms. |
| 14 | **3-Way Match** | **LIVE** | `three_way_match.py` deterministically compares PO Amount/Qty $\leftrightarrow$ GRN Qty $\leftrightarrow$ Invoice Amount/Qty. Sets status to `MATCHED` or `DISCREPANCY`. Supports manual override with audit log. |
| 15 | **Payment Due Calculation** | **LIVE** | `due_date = invoice_date + payment_terms` (15, 30, 45, 60 days). Separate from 3-day SLA escalation alert threshold. |
| 16 | **Audit Events** | **LIVE** | `audit_service.py` records actor, action, entity_type, entity_id, old_value, new_value, timestamp, and correlation ID for all state changes. |
| 17 | **Notifications** | **LIVE** | `notification.py` model and `/api/notifications` API log real-time in-app alerts on exceptions, approvals, and stock risks. |
| 18 | **Demo Mode** | **LIVE** | `demo.py` provides `POST /api/demo/reset` (XLR-500 end-to-end scenario) and `POST /api/demo/trigger-exceptions` (Exception Demo scenario). |
| 19 | **Role-Based Authorization** | **LIVE** | Enforced via `require_roles(...)` dependency in `dependencies.py`. Unallowed requests return **HTTP 403 Forbidden**. Navigation filtered by role in `Sidebar.tsx`. |
| 20 | **AI Quote Extraction** | **PARTIALLY LIVE** | Endpoint `/api/ai/extract-quote` parses text/PDF, validates schema, flags missing fields with `NEEDS_REVIEW`, and falls back to clearly labeled DEMO/FALLBACK mode if no API key is provided. |

---

## 2. Verification Classification Summary

- **LIVE**: 19 / 20 Features
- **PARTIALLY LIVE**: 1 / 20 Features (AI Quote Extraction with fallback)
- **SEEDED / STATIC / MISSING**: 0 Features

All core business workflow steps are functional with live API and database state persistence.
