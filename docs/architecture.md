# Architecture Document

## 1. Business Problem

Manufacturing procurement workflows are overwhelmingly manual. SCM professionals spend most of their time on repetitive tasks — creating requirements, collecting supplier quotes via email, comparing prices in spreadsheets, chasing approvals, manually creating POs in SAP, verifying deliveries, matching invoices, and monitoring payments. This leads to:

- **Slow cycle times** (days-to-weeks for routine procurements)
- **High error rates** in manual data entry and invoice matching
- **Poor visibility** into procurement pipeline status
- **Missed payment deadlines** and strained supplier relationships
- **Inability to identify savings** across categories and suppliers

## 2. Proposed Solution

An **AI-enabled SCM Procurement Control Tower** that:

1. Provides a single-pane-of-glass view of the entire procurement lifecycle
2. Automates routine processing (quote comparison, invoice validation, payment scheduling)
3. Surfaces only exceptions, risks, and decisions requiring human judgment
4. Integrates with SAP for PO creation, GRN posting, and invoice processing
5. Maintains a complete audit trail for compliance

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React/Vite)                 │
│   Login · Dashboard · Requirements · Suppliers · POs    │
│   Quotes · Approvals · Inventory · Invoices · Payments  │
└───────────────────┬─────────────────────────────────────┘
                    │ REST API (JWT Auth)
┌───────────────────▼─────────────────────────────────────┐
│              FastAPI Backend (Python)                    │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐   │
│  │ API Layer│  │  Services  │  │  Business Rules   │   │
│  │ (Routes) │→ │  (Logic)   │→ │  (Deterministic)  │   │
│  └──────────┘  └─────┬──────┘  └───────────────────┘   │
│                      │                                   │
│  ┌───────────────────▼──────────────────────────────┐   │
│  │            SAP Adapter (Interface)                │   │
│  │   MockSAPAdapter  ←→  (future: RealSAPAdapter)   │   │
│  └───────────────────┬──────────────────────────────┘   │
│                      │                                   │
│  ┌───────────────────▼──────────────────────────────┐   │
│  │         PostgreSQL (via SQLAlchemy/Alembic)       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│              Mock SAP Service (FastAPI)                  │
│   Simulates: POs, GRNs, Invoices, Materials, Inventory  │
│   In-memory data store with realistic seed data          │
└─────────────────────────────────────────────────────────┘
```

## 4. Data Flow

```
Requirement → RFQ → Supplier Quotes → Comparison → Approval
→ Purchase Order → SAP Sync → Goods Receipt → Inventory Update
→ Invoice → 3-Way Match → Payment → Finance Approval → Completion
```

Every state transition is:
- Recorded in the audit log
- Validated by deterministic business rules
- Visible on the control tower dashboard

## 5. Component Responsibilities

| Component | Responsibility | Does NOT do |
|-----------|---------------|-------------|
| **Frontend** | UI rendering, user interaction, form validation | Business logic, calculations, direct SAP calls |
| **FastAPI Backend** | Business rules, calculations, orchestration, API contracts | UI rendering, direct SAP protocol |
| **SAP Adapter** | Abstract SAP communication interface | Business decisions |
| **Mock SAP** | Simulate SAP responses with realistic data | Production SAP operations |
| **PostgreSQL** | Persistent operational data, audit trail | File storage, caching |
| **n8n (future)** | Workflow orchestration, integrations, scheduling | Business rules, data storage |
| **AI (future)** | Extract, summarize, draft, recommend | Final decisions, source of truth |

## 6. Mock SAP Explanation

The Mock SAP service is a **separate FastAPI application** that simulates SAP ERP endpoints:
- Maintains in-memory transaction data (POs, GRNs, Invoices)
- Returns realistic response structures matching SAP API patterns
- Runs as an independent Docker container

**Critical design decision**: The main backend communicates with SAP exclusively through the `SAPAdapter` interface. `MockSAPAdapter` implements this interface via HTTP calls to the Mock SAP service. To migrate to real SAP:
1. Implement `RealSAPAdapter` with the same interface
2. Swap the factory function in `sap_adapter.py`
3. No other code changes required

## 7. n8n Future Role

n8n will serve as an **orchestration and integration layer**, NOT a business logic engine:
- Schedule recurring tasks (quote collection reminders, payment due alerts)
- Trigger workflows based on events (new requirement → notify suppliers)
- Integrate with external systems (email, Slack, etc.)
- All business rules remain in the FastAPI backend

## 8. AI Future Role

AI capabilities will be added through a **provider-agnostic interface**:
- **Extract**: Parse unstructured supplier quotes into structured data
- **Summarize**: Generate executive summaries of procurement activity
- **Draft**: Suggest RFQ emails, PO descriptions, approval notes
- **Recommend**: Suggest best supplier based on historical data
- **AI is NEVER the source of truth** — humans approve, deterministic code calculates

## 9. Production Migration Strategy

1. Replace `MockSAPAdapter` with `RealSAPAdapter`
2. Replace local JWT auth with Keycloak/OIDC
3. Replace mock payment service with bank integration
4. Add n8n for workflow orchestration
5. Deploy to cloud (Kubernetes/Docker Swarm)
6. Add monitoring, alerting, and observability

## 10. Security Assumptions

- JWT authentication for the prototype (Keycloak-ready interface)
- Role-based access control (SCM_USER, PROCUREMENT_MANAGER, FINANCE_USER, ADMIN)
- No secrets in source code (all via environment variables)
- CORS restricted to known frontend origins
- Audit log captures all state-changing operations
- No real SAP credentials stored or transmitted
- No real bank credentials stored or transmitted
