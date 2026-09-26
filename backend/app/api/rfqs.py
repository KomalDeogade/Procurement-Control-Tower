"""RFQ API – generate and manage RFQs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.rfq import RFQ, RFQStatus
from app.models.requirement import Requirement, RequirementStatus
from app.models.user import User
from app.schemas import RFQCreate, RFQResponse
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/", response_model=list[RFQResponse])
async def list_rfqs(
    requirement_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(RFQ).order_by(RFQ.created_at.desc())
    if requirement_id:
        q = q.where(RFQ.requirement_id == requirement_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=RFQResponse, status_code=201)
async def create_rfq(
    body: RFQCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Generate display_id
    all_rfqs = (await db.execute(select(RFQ))).scalars().all()
    display_id = f"RFQ-{3001 + len(all_rfqs)}"

    rfq = RFQ(display_id=display_id, status=RFQStatus.SENT, **body.model_dump())
    db.add(rfq)

    # Update requirement status
    req = (await db.execute(select(Requirement).where(Requirement.id == body.requirement_id))).scalar_one_or_none()
    if req and req.status in ("SUBMITTED",):
        req.status = RequirementStatus.RFQ_IN_PROGRESS

    await log_audit(db, current_user.username, "CREATE", "rfq", display_id,
                    new_value={"requirement_id": body.requirement_id, "supplier_id": body.supplier_id})
    await db.commit()
    await db.refresh(rfq)
    return rfq


@router.post("/generate/{requirement_id}")
async def generate_rfqs(
    requirement_id: int,
    supplier_ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate RFQs for multiple suppliers at once."""
    req = (await db.execute(select(Requirement).where(Requirement.id == requirement_id))).scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")

    all_rfqs = (await db.execute(select(RFQ))).scalars().all()
    counter = 3001 + len(all_rfqs)
    created = []

    for sid in supplier_ids:
        rfq = RFQ(
            display_id=f"RFQ-{counter}",
            requirement_id=requirement_id,
            supplier_id=sid,
            status=RFQStatus.SENT,
        )
        db.add(rfq)
        created.append(f"RFQ-{counter}")
        counter += 1

    if req.status in ("SUBMITTED",):
        req.status = RequirementStatus.RFQ_IN_PROGRESS

    await log_audit(db, current_user.username, "GENERATE_RFQS", "requirement",
                    req.display_id or str(req.id),
                    new_value={"rfqs_created": created, "supplier_count": len(supplier_ids)})
    await db.commit()
    return {"message": f"Generated {len(created)} RFQs", "rfq_ids": created}


@router.get("/token/{token}", response_model=RFQResponse)
async def get_rfq_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Tokenized public endpoint – no auth required. Secure single-RFQ access."""
    result = await db.execute(select(RFQ).where(RFQ.access_token == token))
    rfq = result.scalar_one_or_none()
    if not rfq:
        # Fallback to ID search for legacy integer tokens
        if token.isdigit():
            result = await db.execute(select(RFQ).where(RFQ.id == int(token)))
            rfq = result.scalar_one_or_none()
    if not rfq:
        raise HTTPException(404, "RFQ not found or token expired")
    return rfq


@router.get("/public/{rfq_id}", response_model=RFQResponse)
async def get_rfq_public(
    rfq_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint – no auth required. Used by supplier portal."""
    result = await db.execute(select(RFQ).where(RFQ.id == rfq_id))
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise HTTPException(404, "RFQ not found")
    return rfq


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(
    rfq_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RFQ).where(RFQ.id == rfq_id))
    rfq = result.scalar_one_or_none()
    if not rfq:
        raise HTTPException(404, "RFQ not found")
    return rfq
