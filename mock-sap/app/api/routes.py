"""
Mock SAP API Routes – simulating real SAP ERP endpoints.

Maintains in-memory data for the prototype.
No real SAP connectivity.  No real SAP credentials.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
#  In-memory data store (realistic manufacturing seed data)
# ═══════════════════════════════════════════════════════════════

_suppliers = [
    {"supplier_id": "SUP-001", "name": "Acme Steel Corp", "location": "Mumbai, India", "category": "Raw Materials", "status": "ACTIVE"},
    {"supplier_id": "SUP-002", "name": "Precision Bearings Ltd", "location": "Chennai, India", "category": "Components", "status": "ACTIVE"},
    {"supplier_id": "SUP-003", "name": "Global Fasteners Inc", "location": "Pune, India", "category": "Fasteners", "status": "ACTIVE"},
    {"supplier_id": "SUP-004", "name": "ElectroParts GmbH", "location": "Stuttgart, Germany", "category": "Electronics", "status": "ACTIVE"},
    {"supplier_id": "SUP-005", "name": "Pacific Polymers", "location": "Shanghai, China", "category": "Polymers", "status": "ACTIVE"},
]

_materials = [
    {"material_code": "MAT-10001", "name": "Carbon Steel Sheet 2mm", "unit": "KG", "category": "Raw Materials", "price": 85.0},
    {"material_code": "MAT-10002", "name": "Ball Bearing 6205", "unit": "PCS", "category": "Components", "price": 12.50},
    {"material_code": "MAT-10003", "name": "Hex Bolt M10x50 SS304", "unit": "PCS", "category": "Fasteners", "price": 2.75},
    {"material_code": "MAT-10004", "name": "PLC Controller Unit", "unit": "PCS", "category": "Electronics", "price": 450.0},
    {"material_code": "MAT-10005", "name": "Nylon 6 Granules", "unit": "KG", "category": "Polymers", "price": 3.20},
    {"material_code": "MAT-10006", "name": "Hydraulic Cylinder 50mm", "unit": "PCS", "category": "Components", "price": 320.0},
    {"material_code": "MAT-10007", "name": "Copper Wire 1.5mm", "unit": "MTR", "category": "Raw Materials", "price": 1.80},
    {"material_code": "MAT-10008", "name": "Servo Motor 2kW", "unit": "PCS", "category": "Electronics", "price": 890.0},
]

_inventory = [
    {"material_code": "MAT-10001", "plant": "PLANT-01", "warehouse": "WH-A", "quantity": 5000, "unit": "KG", "reorder_level": 1000},
    {"material_code": "MAT-10002", "plant": "PLANT-01", "warehouse": "WH-B", "quantity": 2500, "unit": "PCS", "reorder_level": 500},
    {"material_code": "MAT-10003", "plant": "PLANT-01", "warehouse": "WH-A", "quantity": 15000, "unit": "PCS", "reorder_level": 3000},
    {"material_code": "MAT-10004", "plant": "PLANT-02", "warehouse": "WH-C", "quantity": 45, "unit": "PCS", "reorder_level": 10},
    {"material_code": "MAT-10005", "plant": "PLANT-01", "warehouse": "WH-D", "quantity": 8000, "unit": "KG", "reorder_level": 2000},
]

# Auto-incrementing counters
_po_counter = 450001000
_grn_counter = 500001000
_invoice_counter = 220001000
_purchase_orders: dict[str, dict] = {}
_goods_receipts: list[dict] = []
_invoices: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════
#  Request/Response Models
# ═══════════════════════════════════════════════════════════════

class PurchaseOrderRequest(BaseModel):
    supplier_id: str
    material_code: str
    quantity: float
    unit_price: float
    requirement_id: Optional[str] = None


class GoodsReceiptRequest(BaseModel):
    purchase_order_number: str
    received_quantity: float
    quality_status: str = "PASSED"


class InvoiceRequest(BaseModel):
    purchase_order_number: str
    invoice_amount: float
    tax_amount: float = 0.0


# ═══════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════

@router.get("/suppliers")
async def get_suppliers():
    return _suppliers


@router.get("/materials")
async def get_materials():
    return _materials


@router.get("/inventory")
async def get_inventory():
    return _inventory


@router.post("/purchase-requisitions")
async def create_purchase_requisition(data: dict):
    """Accept a purchase requisition (simplified simulation)."""
    return {
        "status": "SUCCESS",
        "message": "Purchase requisition received",
        "data": data,
    }


@router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderRequest):
    global _po_counter
    _po_counter += 1
    po_number = str(_po_counter)
    now = datetime.now(timezone.utc).isoformat()

    po = {
        "purchase_order_number": po_number,
        "supplier_id": data.supplier_id,
        "material_code": data.material_code,
        "quantity": data.quantity,
        "unit_price": data.unit_price,
        "total_amount": data.quantity * data.unit_price,
        "requirement_id": data.requirement_id,
        "status": "CREATED",
        "created_at": now,
    }
    _purchase_orders[po_number] = po

    return {
        "status": "SUCCESS",
        "purchase_order_number": po_number,
        "created_at": now,
        "message": "Purchase Order created successfully",
    }


@router.get("/purchase-orders/{po_number}")
async def get_purchase_order(po_number: str):
    po = _purchase_orders.get(po_number)
    if not po:
        raise HTTPException(status_code=404, detail=f"PO {po_number} not found")
    return po


@router.post("/goods-receipts")
async def create_goods_receipt(data: GoodsReceiptRequest):
    global _grn_counter
    _grn_counter += 1
    grn_number = str(_grn_counter)
    now = datetime.now(timezone.utc).isoformat()

    grn = {
        "grn_number": grn_number,
        "purchase_order_number": data.purchase_order_number,
        "received_quantity": data.received_quantity,
        "quality_status": data.quality_status,
        "created_at": now,
    }
    _goods_receipts.append(grn)

    # Update PO status
    po = _purchase_orders.get(data.purchase_order_number)
    if po:
        po["status"] = "GOODS_RECEIVED"

    return {
        "status": "SUCCESS",
        "grn_number": grn_number,
        "created_at": now,
        "message": "Goods Receipt recorded successfully",
    }


@router.post("/invoices")
async def create_invoice(data: InvoiceRequest):
    global _invoice_counter
    _invoice_counter += 1
    inv_number = str(_invoice_counter)
    now = datetime.now(timezone.utc).isoformat()

    invoice = {
        "invoice_number": inv_number,
        "purchase_order_number": data.purchase_order_number,
        "invoice_amount": data.invoice_amount,
        "tax_amount": data.tax_amount,
        "total_amount": data.invoice_amount + data.tax_amount,
        "status": "RECEIVED",
        "created_at": now,
    }
    _invoices[inv_number] = invoice

    return {
        "status": "SUCCESS",
        "invoice_number": inv_number,
        "created_at": now,
        "message": "Invoice recorded successfully",
    }


@router.get("/invoices/{invoice_number}")
async def get_invoice(invoice_number: str):
    inv = _invoices.get(invoice_number)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")
    return inv


@router.get("/payment-status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Simulate payment status lookup."""
    return {
        "payment_id": payment_id,
        "status": "PENDING",
        "message": "Payment is being processed (mock simulation)",
    }
