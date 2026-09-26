"""Requirements API – full CRUD with audit trail."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.requirement import Requirement, RequirementStatus
from app.models.user import User
from app.schemas import RequirementCreate, RequirementUpdate, RequirementResponse
from app.services.audit_service import log_audit

router = APIRouter()

_counter_cache = {"val": 1001}


@router.get("/", response_model=list[RequirementResponse])
async def list_requirements(
    status: str | None = None,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Requirement).order_by(Requirement.created_at.desc())
    if status:
        q = q.where(Requirement.status == status)
    if priority:
        q = q.where(Requirement.priority == priority)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=RequirementResponse, status_code=201)
async def create_requirement(
    body: RequirementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get next display_id
    count_res = await db.execute(select(Requirement))
    all_reqs = count_res.scalars().all()
    next_num = 1001 + len(all_reqs)
    display_id = f"REQ-{next_num}"

    req = Requirement(
        display_id=display_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(req)
    await db.flush()
    await log_audit(db, current_user.username, "CREATE", "requirement", display_id,
                    new_value={"material": req.material_name, "quantity": req.quantity, "status": "DRAFT"})
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/{req_id}", response_model=RequirementResponse)
async def get_requirement(
    req_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")
    return req


@router.patch("/{req_id}", response_model=RequirementResponse)
async def update_requirement(
    req_id: int,
    body: RequirementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")

    old_status = req.status
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(req, field, value)

    await log_audit(db, current_user.username, "UPDATE", "requirement",
                    req.display_id or str(req.id),
                    old_value={"status": str(old_status)},
                    new_value=updates)
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{req_id}/submit", response_model=RequirementResponse)
async def submit_requirement(
    req_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")
    if req.status not in ("DRAFT",):
        raise HTTPException(400, f"Cannot submit from status {req.status}")
    req.status = RequirementStatus.SUBMITTED
    await log_audit(db, current_user.username, "SUBMIT", "requirement",
                    req.display_id or str(req.id),
                    old_value={"status": "DRAFT"}, new_value={"status": "SUBMITTED"})
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/{req_id}/timeline")
async def get_requirement_timeline(
    req_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the end-to-end timeline for a requirement."""
    from app.models.audit_log import AuditLog
    from app.models.rfq import RFQ
    from app.models.supplier_quote import SupplierQuote
    from app.models.approval import Approval
    from app.models.purchase_order import PurchaseOrder
    from app.models.goods_receipt import GoodsReceipt
    from app.models.invoice import Invoice
    from app.models.payment import Payment

    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")

    timeline = []
    timeline.append({"step": "Requirement Created", "status": "completed",
                      "date": str(req.created_at), "detail": req.display_id})

    # RFQs
    rfqs = (await db.execute(select(RFQ).where(RFQ.requirement_id == req_id))).scalars().all()
    if rfqs:
        timeline.append({"step": "RFQ Sent", "status": "completed",
                          "date": str(rfqs[0].created_at), "detail": f"{len(rfqs)} suppliers"})

    # Quotes
    qs = (await db.execute(select(SupplierQuote).where(SupplierQuote.requirement_id == req_id))).scalars().all()
    if qs:
        timeline.append({"step": "Quotes Received", "status": "completed",
                          "date": str(qs[0].submitted_at or qs[0].created_at), "detail": f"{len(qs)} quotes"})

    # Approval
    apprs = (await db.execute(select(Approval).where(
        Approval.entity_type == "requirement", Approval.entity_id == req_id
    ))).scalars().all()
    if apprs:
        for a in apprs:
            timeline.append({"step": "Approval", "status": str(a.status).lower(),
                              "date": str(a.approved_at or a.created_at), "detail": str(a.status)})

    # POs
    po_list = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.requirement_id == req_id))).scalars().all()
    if po_list:
        for po in po_list:
            timeline.append({"step": "PO Created", "status": "completed",
                              "date": str(po.created_at), "detail": po.display_id})
            if po.sap_po_number:
                timeline.append({"step": "SAP Synchronized", "status": "completed",
                                  "date": str(po.created_at), "detail": f"SAP PO: {po.sap_po_number}"})

            # GRNs
            grn_list = (await db.execute(select(GoodsReceipt).where(GoodsReceipt.po_id == po.id))).scalars().all()
            for grn in grn_list:
                timeline.append({"step": "Goods Received", "status": "completed",
                                  "date": str(grn.created_at), "detail": grn.display_id})

            # Invoices
            inv_list = (await db.execute(select(Invoice).where(Invoice.po_id == po.id))).scalars().all()
            for inv in inv_list:
                timeline.append({"step": "Invoice Received", "status": "completed",
                                  "date": str(inv.created_at), "detail": inv.display_id})
                # 3-way match
                timeline.append({"step": "3-Way Match", "status": str(inv.status).lower(),
                                  "date": str(inv.created_at), "detail": str(inv.status)})

                # Payments
                pay_list = (await db.execute(select(Payment).where(Payment.invoice_id == inv.id))).scalars().all()
                for pay in pay_list:
                    timeline.append({"step": "Payment", "status": str(pay.status).lower(),
                                      "date": str(pay.created_at), "detail": pay.display_id})

    return {"requirement_id": req_id, "display_id": req.display_id, "timeline": timeline}
