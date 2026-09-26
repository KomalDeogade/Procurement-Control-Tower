"""Dashboard API – KPIs, attention items, and summary statistics."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.requirement import Requirement
from app.models.supplier_quote import SupplierQuote
from app.models.approval import Approval, ApprovalStatus
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.inventory import InventoryItem
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.supplier import Supplier
from app.models.user import User

router = APIRouter()


@router.get("/kpis")
async def dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Main dashboard KPI cards."""
    now = datetime.utcnow()

    # Requirements
    open_reqs = (await db.execute(
        select(func.count()).select_from(Requirement).where(
            Requirement.status.in_(["DRAFT", "SUBMITTED", "RFQ_IN_PROGRESS", "QUOTES_RECEIVED", "UNDER_REVIEW", "APPROVAL_PENDING", "APPROVED"])
        )
    )).scalar() or 0

    # Pending Quotes
    pending_quotes = (await db.execute(
        select(func.count()).select_from(SupplierQuote).where(SupplierQuote.status == "SUBMITTED")
    )).scalar() or 0

    # Pending Approvals
    pending_approvals = (await db.execute(
        select(func.count()).select_from(Approval).where(Approval.status == "PENDING")
    )).scalar() or 0

    # Active POs
    active_pos = (await db.execute(
        select(func.count()).select_from(PurchaseOrder).where(
            PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED", "PARTIALLY_RECEIVED"])
        )
    )).scalar() or 0

    # Stock Risk
    items = (await db.execute(select(InventoryItem))).scalars().all()
    stock_risk_count = 0
    for item in items:
        avail = item.quantity_on_hand - item.reserved_quantity
        if avail <= item.safety_stock:
            stock_risk_count += 1

    # Invoice counts
    invoices_due = (await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED", "APPROVAL_PENDING"]),
            Invoice.due_date <= now + timedelta(days=7),
        )
    )).scalar() or 0

    overdue_invoices = (await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED", "APPROVAL_PENDING"]),
            Invoice.due_date < now,
        )
    )).scalar() or 0

    # Payment Pending
    payment_pending = (await db.execute(
        select(func.count()).select_from(Payment).where(Payment.status == "PENDING")
    )).scalar() or 0

    # Supplier Risk
    supplier_risk = (await db.execute(
        select(func.count()).select_from(Supplier).where(Supplier.risk_score >= 40)
    )).scalar() or 0

    return {
        "open_requirements": open_reqs,
        "pending_quotes": pending_quotes,
        "pending_approvals": pending_approvals,
        "active_purchase_orders": active_pos,
        "stock_risk": stock_risk_count,
        "invoices_due": invoices_due,
        "overdue_invoices": overdue_invoices,
        "payment_pending": payment_pending,
        "supplier_risk": supplier_risk,
    }


@router.get("/attention")
async def todays_attention(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Items requiring human action today."""
    now = datetime.utcnow()
    attention_items = []

    # Pending approvals
    approvals = (await db.execute(
        select(Approval).where(Approval.status == "PENDING")
    )).scalars().all()
    for a in approvals:
        req = None
        if a.entity_type == "requirement":
            req = (await db.execute(select(Requirement).where(Requirement.id == a.entity_id))).scalar_one_or_none()
        attention_items.append({
            "type": "approval",
            "priority": "high",
            "message": f"Approve {'requirement ' + req.display_id if req else a.entity_type + ' #' + str(a.entity_id)}",
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "approval_id": a.id,
        })

    # Invoice mismatches
    discrepancies = (await db.execute(
        select(Invoice).where(Invoice.status == "DISCREPANCY")
    )).scalars().all()
    for inv in discrepancies:
        attention_items.append({
            "type": "invoice_mismatch",
            "priority": "high",
            "message": f"Review invoice mismatch {inv.display_id}",
            "entity_type": "invoice",
            "entity_id": inv.id,
        })

    # Critical stock
    items = (await db.execute(select(InventoryItem))).scalars().all()
    for item in items:
        avail = item.quantity_on_hand - item.reserved_quantity
        if avail <= item.safety_stock:
            attention_items.append({
                "type": "stock_risk",
                "priority": "critical" if avail <= 0 else "high",
                "message": f"Critical stock risk for {item.material_code} ({item.material_name})",
                "entity_type": "inventory",
                "entity_id": item.id,
            })

    # Payments due soon
    due_invoices = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date <= now + timedelta(days=3),
        )
    )).scalars().all()
    for inv in due_invoices:
        due = inv.due_date.replace(tzinfo=None) if inv.due_date else now
        days_left = (due - now).days
        attention_items.append({
            "type": "payment_due",
            "priority": "critical" if days_left <= 0 else "high",
            "message": f"Payment due {'today' if days_left == 0 else 'in ' + str(days_left) + ' days' if days_left > 0 else str(abs(days_left)) + ' days overdue'} for {inv.display_id}",
            "entity_type": "invoice",
            "entity_id": inv.id,
        })

    attention_items.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["priority"], 3))

    return {"count": len(attention_items), "items": attention_items[:20]}
