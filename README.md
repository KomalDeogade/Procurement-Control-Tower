# SCM Procurement Control Tower – Enterprise Upgrade

An **AI-enabled SCM Procurement Control Tower** with deterministic business rules, exception-first automation, Role-Based Access Control (RBAC), Mock SAP ERP integration, and n8n workflow blueprints.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React 18 / Vite)                      │
│   Role-Based Sidebar Navigation · Glassmorphism Dashboard · Exceptions    │
│   Roles: SUPPLIER · SCM_USER · PROCUREMENT_MANAGER · STORE_USER · FINANCE  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ REST API (JWT Bearer Token)
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                        FastAPI Backend (Python 3.14)                       │
│  ┌────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  RBAC Guard (403)  │  │ Deterministic Rules │  │   Scoring Engine    │ │
│  └────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│  ┌────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  3-Way Matcher     │  │ Inventory Analytics │  │  Audit Logger       │ │
│  └────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                     │                                     │
│  ┌──────────────────────────────────▼──────────────────────────────────┐  │
│  │                     SAPAdapter (Abstract Interface)                 │  │
│  │        MockSAPAdapter ◄─────────────────► (Future: RealSAPAdapter)   │  │
│  └──────────────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │ HTTP (Port 8001)
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                      Mock SAP Service (FastAPI)                            │
│   Simulates: POs (450001xxx), GRNs, Invoices, Materials, Inventory        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Role-Based Access Control (RBAC Matrix)

| Role | Visible Navigation & Capabilities | Backend Permission Enforcement |
| :--- | :--- | :--- |
| **SUPPLIER** | Dashboard, My RFQs, My Quotes, My Orders, My Deliveries | Isolated to assigned supplier data only. Cannot view directory or other suppliers. |
| **SCM_USER** | Dashboard, Requirements, Suppliers, RFQs, Quote Comparison, POs, Inventory, Exceptions, Reports | Full procurement requisition & quote comparison capabilities. |
| **PROCUREMENT_MANAGER** | Dashboard, Approvals, Suppliers, POs, Exceptions, Reports | High-value budget approvals, vendor verification, policy override. |
| **STORE_USER** | Dashboard, Goods Receipts (GRN), Inventory, Exceptions | Physical receiving inspection, stock count management. |
| **FINANCE_USER** | Dashboard, Invoices, 3-Way Match, Payments, Exceptions, Reports | Invoice discrepancy verification, payment authorization & UTR execution. |
| **ADMIN** | All Navigation, System Config, Users, Audit Trail, Health | Complete administrative oversight & system integration configuration. |

---

## ⚡ Quick Start Guide (Local Development)

### 1. Start Backend & Database
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed_data
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API**: `http://localhost:8000/api`
- **Swagger Documentation**: `http://localhost:8000/docs`

### 2. Start Mock SAP Service
```powershell
cd mock-sap
..\backend\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
- **Mock SAP Base URL**: `http://localhost:8001`
- **Mock SAP Health Check**: `http://localhost:8001/health`

### 3. Start Frontend App
```powershell
cd frontend
npm install
npm run dev
```
- **Control Tower Web UI**: `http://localhost:5173`

---

## 🧪 Running Automated Unit Tests

```powershell
cd backend
.\.venv\Scripts\pytest -v
```
*(Runs 117 unit tests covering RBAC authorization, scoring, inventory calculations, 3-way match, and payment logic)*

---

## 🐳 Running via Docker Compose

```bash
docker compose up -d
```
Starts PostgreSQL database, FastAPI Backend, and Mock SAP Service in isolated containers.

---

## 🔄 n8n Integration Workflows

The `n8n/` directory contains 3 production-ready workflow blueprints:
1. `n8n/rfq_automation.json` – Automated RFQ generation & notifications upon Requirement approval.
2. `n8n/quote_processing.json` – Automated quote extraction & scoring pipeline upon supplier submission.
3. `n8n/morning_monitoring.json` – Daily 8:00 AM scheduled job triggering AI Procurement Brief & exception aggregation.
