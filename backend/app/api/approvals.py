"""Approvals API – manager and finance approval workflows."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.approval import Approval, ApprovalStatus
from app.models.requirement import Requirement, RequirementStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas import ApprovalCreate, ApprovalAction, ApprovalResponse
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/", response_model=list[ApprovalResponse])
async def list_approvals(
    status: str | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Approval).order_by(Approval.created_at.desc())
    if status:
        q = q.where(Approval.status == status)
    if entity_type:
        q = q.where(Approval.entity_type == entity_type)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    body: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_apprs = (await db.execute(select(Approval))).scalars().all()
    display_id = f"APR-{7001 + len(all_apprs)}"

    approval = Approval(
        display_id=display_id,
        status=ApprovalStatus.PENDING,
        **body.model_dump(),
    )
    db.add(approval)

    # Update entity status
    if body.entity_type == "requirement":
        req = (await db.execute(select(Requirement).where(Requirement.id == body.entity_id))).scalar_one_or_none()
        if req:
            req.status = RequirementStatus.APPROVAL_PENDING

    await log_audit(db, current_user.username, "CREATE_APPROVAL", body.entity_type, str(body.entity_id),
                    new_value={"approval_id": display_id, "approver_id": body.approver_id})
    await db.commit()
    await db.refresh(approval)
    return approval


@router.patch("/{approval_id}", response_model=ApprovalResponse)
async def action_approval(
    approval_id: int,
    body: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(404, "Approval not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(400, f"Approval already processed: {approval.status}")

    old_status = approval.status
    approval.status = body.status
    approval.comments = body.comments
    if body.status == "APPROVED":
        approval.approved_at = datetime.now(timezone.utc)

    # Update related entity
    if approval.entity_type == "requirement":
        req = (await db.execute(select(Requirement).where(Requirement.id == approval.entity_id))).scalar_one_or_none()
        if req:
            if body.status == "APPROVED":
                req.status = RequirementStatus.APPROVED
            elif body.status == "REJECTED":
                req.status = RequirementStatus.REJECTED
    elif approval.entity_type == "invoice":
        inv = (await db.execute(select(Invoice).where(Invoice.id == approval.entity_id))).scalar_one_or_none()
        if inv:
            if body.status == "APPROVED":
                inv.status = InvoiceStatus.APPROVED
            elif body.status == "REJECTED":
                inv.status = InvoiceStatus.REJECTED

    await log_audit(db, current_user.username, body.status, approval.entity_type,
                    approval.display_id or str(approval.id),
                    old_value={"status": str(old_status)},
                    new_value={"status": body.status, "comments": body.comments})
    await db.commit()
    await db.refresh(approval)
    return approval


@router.get("/{approval_id}/detail")
async def get_approval_detail(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get approval with full context (requirement, quotes, comparison)."""
    from app.models.supplier_quote import SupplierQuote
    from app.models.supplier import Supplier

    approval = (await db.execute(select(Approval).where(Approval.id == approval_id))).scalar_one_or_none()
    if not approval:
        raise HTTPException(404, "Approval not found")

    detail = {"approval": ApprovalResponse.model_validate(approval).model_dump()}

    if approval.entity_type == "requirement":
        req = (await db.execute(select(Requirement).where(Requirement.id == approval.entity_id))).scalar_one_or_none()
        if req:
            from app.schemas import RequirementResponse
            detail["requirement"] = RequirementResponse.model_validate(req).model_dump()

            # Get quotes and scores
            quotes = (await db.execute(
                select(SupplierQuote).where(SupplierQuote.requirement_id == req.id)
            )).scalars().all()
            detail["quotes"] = [QuoteResponse.model_validate(q).model_dump() for q in quotes]

            # Score them
            from app.services.scoring_service import score_suppliers, generate_explanation
            scoring_input = []
            for q in quotes:
                supplier = (await db.execute(select(Supplier).where(Supplier.id == q.supplier_id))).scalar_one_or_none()
                scoring_input.append({
                    "supplier_id": q.supplier_id,
                    "supplier_name": supplier.company_name if supplier else "Unknown",
                    "unit_price": q.unit_price, "total_price": q.total_price, "quantity": q.quantity,
                    "lead_time_days": q.lead_time_days or 30, "availability": q.availability,
                    "payment_terms": q.payment_terms, "warranty": q.warranty,
                    "quality_score": supplier.quality_score if supplier else 50,
                    "delivery_score": supplier.delivery_score if supplier else 50,
                    "risk_score": supplier.risk_score if supplier else 50,
                    "historical_performance": (supplier.quality_score + supplier.delivery_score) / 2 if supplier else 50,
                })
            scored = score_suppliers(scoring_input)
            detail["scores"] = [
                {**s.to_dict(), "explanation": generate_explanation(s)} for s in scored
            ]

    return detail


# Import needed for detail endpoint
from app.schemas import QuoteResponse
