"""Invoices API – management, 3-way matching, payment due monitoring."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.purchase_order import PurchaseOrder
from app.models.goods_receipt import GoodsReceipt
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas import InvoiceCreate, InvoiceResponse
from app.services.audit_service import log_audit
from app.services.three_way_match import three_way_match
from app.services.payment_service import analyze_payment_due

router = APIRouter()


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Invoice).order_by(Invoice.created_at.desc())
    if status:
        q = q.where(Invoice.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_invs = (await db.execute(select(Invoice))).scalars().all()
    display_id = f"INV-{220001 + len(all_invs)}"

    inv = Invoice(
        display_id=display_id,
        status=InvoiceStatus.SUBMITTED,
        **body.model_dump(),
    )
    db.add(inv)
    await log_audit(db, current_user.username, "CREATE", "invoice", display_id,
                    new_value={"po_id": body.po_id, "amount": body.total_amount})
    await db.commit()
    await db.refresh(inv)
    return inv


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return inv


@router.post("/{invoice_id}/three-way-match")
async def perform_three_way_match(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform 3-way match: PO + GRN + Invoice."""
    inv = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    po = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == inv.po_id))).scalar_one_or_none()
    if not po:
        raise HTTPException(404, "Related PO not found")

    grns = (await db.execute(select(GoodsReceipt).where(GoodsReceipt.po_id == po.id))).scalars().all()
    grn_qty = sum(g.received_quantity for g in grns)

    result = three_way_match(
        po_quantity=po.quantity,
        po_unit_price=po.unit_price,
        po_total=po.total_amount,
        grn_quantity=grn_qty,
        invoice_quantity=inv.invoice_amount / inv.total_amount * po.quantity if inv.total_amount > 0 else po.quantity,
        invoice_unit_price=po.unit_price,  # Normalize
        invoice_total=inv.total_amount,
    )

    # Update invoice status based on match
    if result.status == "MATCHED":
        inv.status = InvoiceStatus.VALIDATED
    else:
        inv.status = InvoiceStatus.DISCREPANCY

    await log_audit(db, current_user.username, "THREE_WAY_MATCH", "invoice",
                    inv.display_id or str(inv.id),
                    new_value={"status": result.status, "exceptions": result.exceptions})
    await db.commit()

    return {
        "invoice_id": inv.display_id,
        "match_result": result.to_dict(),
        "po": {"display_id": po.display_id, "quantity": po.quantity, "unit_price": po.unit_price, "total": po.total_amount},
        "grn_total_quantity": grn_qty,
    }


@router.get("/payment-due/monitor")
async def payment_due_monitor(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monitor all invoices for payment due dates."""
    invoices = (await db.execute(
        select(Invoice).where(Invoice.status.in_(["VALIDATED", "APPROVED", "APPROVAL_PENDING", "SUBMITTED"]))
    )).scalars().all()

    due_items = []
    for inv in invoices:
        po = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == inv.po_id))).scalar_one_or_none()
        supplier = (await db.execute(select(Supplier).where(Supplier.id == inv.supplier_id))).scalar_one_or_none()

        if inv.invoice_date:
            info = analyze_payment_due(
                invoice_id=inv.display_id or str(inv.id),
                supplier_name=supplier.company_name if supplier else "Unknown",
                amount=inv.total_amount,
                invoice_date=inv.invoice_date,
                payment_terms=po.payment_terms if po else None,
            )
            due_items.append(info.to_dict())

    # Group by category
    categories = {
        "OVERDUE": [d for d in due_items if d["category"] == "OVERDUE"],
        "DUE_TODAY": [d for d in due_items if d["category"] == "DUE_TODAY"],
        "DUE_1_3_DAYS": [d for d in due_items if d["category"] == "DUE_1_3_DAYS"],
        "DUE_4_7_DAYS": [d for d in due_items if d["category"] == "DUE_4_7_DAYS"],
        "DUE_LATER": [d for d in due_items if d["category"] == "DUE_LATER"],
    }

    return {
        "total_invoices": len(due_items),
        "overdue_count": len(categories["OVERDUE"]),
        "due_today_count": len(categories["DUE_TODAY"]),
        "categories": categories,
    }
