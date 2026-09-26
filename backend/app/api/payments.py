"""Payments API – finance approval, mock payment processing."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.purchase_order import PurchaseOrder
from app.models.goods_receipt import GoodsReceipt
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas import PaymentCreate, PaymentResponse
from app.services.audit_service import log_audit
from app.services.mock_payment_service import process_mock_payment

router = APIRouter()


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Payment).order_by(Payment.created_at.desc())
    if status:
        q = q.where(Payment.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_pays = (await db.execute(select(Payment))).scalars().all()
    display_id = f"PAY-{80001 + len(all_pays)}"

    payment = Payment(
        display_id=display_id,
        status=PaymentStatus.PENDING,
        **body.model_dump(),
    )
    db.add(payment)
    await log_audit(db, current_user.username, "CREATE", "payment", display_id,
                    new_value={"invoice_id": body.invoice_id, "amount": body.amount})
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/{payment_id}/process")
async def process_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process mock payment."""
    payment = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")

    if payment.status not in (PaymentStatus.PENDING,):
        raise HTTPException(400, f"Cannot process payment in status {payment.status}")

    # Get supplier name
    inv = (await db.execute(select(Invoice).where(Invoice.id == payment.invoice_id))).scalar_one_or_none()
    supplier_name = "Unknown"
    if inv:
        supplier = (await db.execute(select(Supplier).where(Supplier.id == inv.supplier_id))).scalar_one_or_none()
        if supplier:
            supplier_name = supplier.company_name

    # Process mock payment
    result = process_mock_payment(
        payment_id=payment.display_id or str(payment.id),
        amount=payment.amount,
        supplier_name=supplier_name,
    )

    payment.status = PaymentStatus.COMPLETED if result.status == "SUCCESS" else PaymentStatus.FAILED
    payment.reference_number = result.transaction_reference
    payment.payment_date = datetime.now(timezone.utc)

    # Update invoice status
    if inv and result.status == "SUCCESS":
        inv.status = InvoiceStatus.PAID

    await log_audit(db, current_user.username, "PROCESS_PAYMENT", "payment",
                    payment.display_id or str(payment.id),
                    new_value=result.to_dict())
    await db.commit()

    return result.to_dict()


@router.get("/{payment_id}/finance-detail")
async def finance_detail(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full finance context for approval."""
    payment = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")

    inv = (await db.execute(select(Invoice).where(Invoice.id == payment.invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    po = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == inv.po_id))).scalar_one_or_none()
    grns = (await db.execute(select(GoodsReceipt).where(GoodsReceipt.po_id == inv.po_id))).scalars().all()
    supplier = (await db.execute(select(Supplier).where(Supplier.id == inv.supplier_id))).scalar_one_or_none()

    # 3-way match result
    from app.services.three_way_match import three_way_match
    grn_qty = sum(g.received_quantity for g in grns)
    match_result = three_way_match(
        po_quantity=po.quantity if po else 0,
        po_unit_price=po.unit_price if po else 0,
        po_total=po.total_amount if po else 0,
        grn_quantity=grn_qty,
        invoice_quantity=po.quantity if po else 0,
        invoice_unit_price=po.unit_price if po else 0,
        invoice_total=inv.total_amount,
    )

    return {
        "payment": PaymentResponse.model_validate(payment).model_dump(),
        "invoice": {
            "display_id": inv.display_id, "amount": inv.total_amount,
            "status": str(inv.status), "due_date": str(inv.due_date),
        },
        "purchase_order": {
            "display_id": po.display_id if po else None,
            "total": po.total_amount if po else 0,
            "payment_terms": po.payment_terms if po else None,
        },
        "supplier": {"name": supplier.company_name if supplier else "Unknown"},
        "grn_total_received": grn_qty,
        "three_way_match": match_result.to_dict(),
    }
