# API Contracts

## Base URL

```
Backend:   http://localhost:8000/api
Mock SAP:  http://localhost:8001/sap
```

---

## Authentication

### POST /api/auth/login
Login and receive a JWT token.

**Request:**
```json
{ "username": "admin", "password": "admin123" }
```

**Response (200):**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### POST /api/auth/register
Register a new user.

**Request:**
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "full_name": "New User",
  "password": "secure123",
  "role": "SCM_USER"
}
```

### GET /api/auth/me
Get current authenticated user. Requires `Authorization: Bearer <token>`.

---

## Requirements

### GET /api/requirements
List all requirements. **Auth required.**

### POST /api/requirements
Create a new requirement. **Auth required.**

**Request:**
```json
{
  "material_code": "MAT-10001",
  "material_name": "Carbon Steel Sheet 2mm",
  "quantity": 500,
  "unit": "KG",
  "plant": "PLANT-01",
  "required_by_date": "2025-03-15T00:00:00",
  "budget": 42500.00,
  "currency": "USD",
  "priority": "HIGH"
}
```

**Response (201):**
```json
{
  "id": 1,
  "display_id": "REQ-1001",
  "material_code": "MAT-10001",
  "status": "DRAFT",
  "...": "..."
}
```

### GET /api/requirements/{id}
### PATCH /api/requirements/{id}

---

## Suppliers

### GET /api/suppliers
### POST /api/suppliers
### GET /api/suppliers/{id}
### PATCH /api/suppliers/{id}

---

## Quotes

### GET /api/quotes
### POST /api/quotes
### GET /api/quotes/{id}
*Phase 2 implementation*

---

## Approvals

### GET /api/approvals
### POST /api/approvals
### PATCH /api/approvals/{id}
*Phase 2 implementation*

---

## Purchase Orders

### GET /api/purchase-orders
### POST /api/purchase-orders
### GET /api/purchase-orders/{id}
*Phase 2 implementation*

---

## Inventory

### GET /api/inventory
### GET /api/inventory/{id}
*Phase 2 implementation*

---

## Goods Receipts

### GET /api/goods-receipts
### POST /api/goods-receipts
*Phase 2 implementation*

---

## Invoices

### GET /api/invoices
### POST /api/invoices
### GET /api/invoices/{id}
*Phase 2 implementation*

---

## Payments

### GET /api/payments
### POST /api/payments
### GET /api/payments/{id}
*Phase 2 implementation*

---

## Dashboard

### GET /api/dashboard/summary
Returns aggregated KPIs.

**Response:**
```json
{
  "total_requirements": 0,
  "active_suppliers": 0,
  "open_purchase_orders": 0,
  "pending_approvals": 0,
  "total_spend": 0.0,
  "pending_invoices": 0,
  "overdue_payments": 0
}
```

---

## Audit Log

### GET /api/audit
*Phase 2 implementation*

---

## Health Checks

### GET /api/health
```json
{ "status": "healthy", "service": "scm-backend", "version": "0.1.0" }
```

### GET http://localhost:8001/health
```json
{ "status": "healthy", "service": "mock-sap", "version": "0.1.0" }
```

---

## Mock SAP Endpoints

### GET /sap/suppliers
### GET /sap/materials
### GET /sap/inventory
### POST /sap/purchase-requisitions
### POST /sap/purchase-orders
### GET /sap/purchase-orders/{id}
### POST /sap/goods-receipts
### POST /sap/invoices
### GET /sap/invoices/{id}
### GET /sap/payment-status/{id}
