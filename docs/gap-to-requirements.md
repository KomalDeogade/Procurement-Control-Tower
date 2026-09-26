# SCM Procurement Control Tower – Gap Analysis & Upgrade Plan

Date: September 26, 2026
Purpose: Gap analysis mapping current implementation to requested Phase 2 - Phase 22 requirements.

---

## 1. Requirement vs. Implementation Gap Matrix

| Requirement Phase | Status | Gaps Identified | Upgrade Action Required |
| :--- | :---: | :--- | :--- |
| **Phase 2: RBAC & Security** | Gap Exists | `UserRole` enum lacks `SUPPLIER` & `STORE_USER`. Backend dependencies lack role-permission guards. Frontend displays identical sidebar for all users. Supplier data isolation missing. | Update `UserRole` enum, add `supplier_id` link to `User` model, create role guard dependencies (`require_roles(...)`), add RBAC tests, implement role-specific sidebar navigation. |
| **Phase 3: End-to-End Live Workflow** | Partial | End-to-end flow works via seed script, but needs single correlation ID (`REQ-XXXX`) tracking across all entities and transaction timeline UI. | Ensure `requirement_id` propagates through RFQ $\rightarrow$ Quote $\rightarrow$ Approval $\rightarrow$ PO $\rightarrow$ GRN $\rightarrow$ Invoice $\rightarrow$ Payment, add transaction timeline UI on Requirement detail view. |
| **Phase 4: Secure Supplier Portal** | Gap Exists | Portal currently uses public numeric ID `/supplier/rfq/1` with no token verification or supplier data isolation. | Add secure token generation (`token` column in RFQ), change URL to `/supplier/rfq/<token>`, enforce single-RFQ data isolation in backend. |
| **Phase 5: Deterministic Scoring** | Minor Gap | Scoring engine exists in `scoring_service.py`, but weights need strict alignment to prompt specs (Price 30%, Delivery 20%, Quality 15%, Performance 15%, Terms 10%, Availability 5%, Risk 5%). | Update weights in `scoring_service.py`, format natural-language AI explanation without recalculating score. |
| **Phase 6: Real AI PDF Quotation Extraction** | Missing | AI endpoint exists, but document upload & PDF extraction to structured JSON with Pydantic validation is missing. | Implement `/api/ai/extract-quote-pdf` endpoint with Pydantic schema validation and fallback handling. |
| **Phase 7: Mock SAP Integration** | Implemented | `mock-sap/` microservice runs on port 8001 via `MockSAPAdapter`. | Verify SAP PO creation returns reference (e.g. `450001001`) and displays `Status: SYNCHRONIZED` on PO detail view. |
| **Phase 8: Inventory Risk Intelligence** | Minor Gap | Stock safety level tracked, but deterministic calculation of coverage days, projected stockout date, and reorder qty explanation needs refinement. | Update `inventory_service.py` with exact deterministic formulas: `avail = stock - reserved`, `coverage_days = avail / daily_consumption`, `projected_stockout_date = today + coverage_days`. |
| **Phase 9: Prepaid Supplier Workflow** | Missing | Prepaid balance tracking and advance payment exception trigger missing. | Add `prepaid_balance`, `minimum_balance` to `Supplier`, create advance payment risk exception rule when balance is below threshold. |
| **Phase 10: 3-Way Match Controls & Override** | Minor Gap | 3-Way match logic exists, but manual discrepancy override with audit reason & approval is missing. | Add `/api/invoices/{id}/override` endpoint requiring user, reason, timestamp, and audit logging. |
| **Phase 11: Configurable Payment Terms** | Gap Exists | Hardcoded payment rules. Needs configurable terms (15, 30, 45, 60 days) where `due_date = invoice_date + payment_terms`. | Add `payment_terms` field to `Invoice`, compute `due_date` dynamically, separate 3-day SLA alert from payment terms. |
| **Phase 12: n8n Integration** | Missing | `n8n/` folder contains only `.gitkeep`. | Export 3 production-ready n8n workflow JSON blueprints (`rfq_automation.json`, `quote_processing.json`, `morning_monitoring.json`) calling FastAPI APIs. |
| **Phase 13 & 14: Exception-First Dashboard & AI Brief** | Implemented | Good Morning dashboard, exception feed, and AI Brief exist. | Connect AI Brief to live backend metrics and ensure zero invented metrics. |
| **Phase 15: AI Negotiation Drafter** | Implemented | `ai_features.py` drafts emails based on budget and quote. | Maintain existing UI & backend endpoint (`/api/ai/draft-negotiation`). |
| **Phase 16 & 17: Event Alerts & Audit Trail** | Partial | Audit logging exists (`audit_service.py`). | Ensure single event creates notification, exception, and audit record with correlation ID. |
| **Phase 18: Enhanced Demo Mode** | Partial | Full e2e demo exists in `demo.py`. | Add "Run Exception Demo" triggering intentional supplier delay, invoice mismatch, stockout risk, payment due soon, and advance payment risk. |
| **Phase 19: Impact Metrics** | Partial | Metrics present in reports. | Expose Process Impact metrics calculated from actual workflow events. |
| **Phase 20: Testing** | Partial | 110 unit tests pass. | Add RBAC authorization tests, supplier data isolation tests, 3-way match override tests, and end-to-end pipeline test. |

---

## 2. Execution Plan

We will proceed with executing the upgrades across the codebase in structured steps:
1. **Phase 2 (RBAC & Roles)**: Update `UserRole` enum (`SUPPLIER`, `STORE_USER`), add `supplier_id` column to `User`, create backend role dependencies in `dependencies.py`, update navigation in `AppLayout.tsx` and `App.tsx`, and add authorization tests in `tests/test_rbac_authorization.py`.
2. **Phase 3 & 4 (Live Flow & Secure Supplier Portal)**: Add token column to RFQs, update portal route `/supplier/rfq/:token`, ensure end-to-end execution without manual DB edits.
3. **Phase 5 & 6 (Scoring & AI Quotation Extraction)**: Align scoring weights, implement PDF/JSON document extraction with Pydantic validation.
4. **Phase 7 & 8 (Mock SAP & Inventory Intelligence)**: Verify SAP PO sync UI badges, add stockout coverage days calculation.
5. **Phase 9, 10 & 11 (Prepaid Suppliers, 3-Way Match Override & Payment Terms)**: Add prepaid supplier fields, invoice override API, and configurable payment terms.
6. **Phase 12 (n8n Workflows)**: Create 3 n8n JSON workflow blueprints calling FastAPI endpoints.
7. **Phase 18 & 20 (Exception Demo & Automated Testing)**: Add Exception Demo endpoint and run comprehensive pytest suite.
