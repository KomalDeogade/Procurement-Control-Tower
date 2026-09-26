"""Quotes API – submission (including supplier portal), scoring, comparison."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.supplier_quote import SupplierQuote, QuoteStatus
from app.models.supplier import Supplier
from app.models.requirement import Requirement
from app.models.rfq import RFQ, RFQStatus
from app.models.user import User
from app.schemas import QuoteCreate, QuoteResponse
from app.services.audit_service import log_audit
from app.services.scoring_service import score_suppliers, generate_explanation

router = APIRouter()


@router.get("/", response_model=list[QuoteResponse])
async def list_quotes(
    requirement_id: int | None = None,
    supplier_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SupplierQuote).order_by(SupplierQuote.created_at.desc())
    if requirement_id:
        q = q.where(SupplierQuote.requirement_id == requirement_id)
    if supplier_id:
        q = q.where(SupplierQuote.supplier_id == supplier_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=QuoteResponse, status_code=201)
async def create_quote(
    body: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_quotes = (await db.execute(select(SupplierQuote))).scalars().all()
    display_id = f"QUOTE-{5001 + len(all_quotes)}"

    quote = SupplierQuote(
        display_id=display_id,
        status=QuoteStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    db.add(quote)

    # Update RFQ status
    rfq_result = await db.execute(select(RFQ).where(
        RFQ.requirement_id == body.requirement_id,
        RFQ.supplier_id == body.supplier_id,
    ))
    rfq = rfq_result.scalar_one_or_none()
    if rfq:
        rfq.status = RFQStatus.RESPONDED

    await log_audit(db, current_user.username, "SUBMIT_QUOTE", "quote", display_id,
                    new_value={"supplier_id": body.supplier_id, "total_price": body.total_price})
    await db.commit()
    await db.refresh(quote)
    return quote


@router.post("/supplier-portal")
async def submit_supplier_quote(body: QuoteCreate, db: AsyncSession = Depends(get_db)):
    """Public supplier portal endpoint – no auth required."""
    all_quotes = (await db.execute(select(SupplierQuote))).scalars().all()
    display_id = f"QUOTE-{5001 + len(all_quotes)}"

    quote = SupplierQuote(
        display_id=display_id,
        status=QuoteStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    db.add(quote)

    # Update RFQ
    rfq_result = await db.execute(select(RFQ).where(
        RFQ.requirement_id == body.requirement_id,
        RFQ.supplier_id == body.supplier_id,
    ))
    rfq = rfq_result.scalar_one_or_none()
    if rfq:
        rfq.status = RFQStatus.RESPONDED

    # Update requirement status
    req = (await db.execute(select(Requirement).where(
        Requirement.id == body.requirement_id
    ))).scalar_one_or_none()
    if req and req.status in ("RFQ_IN_PROGRESS", "SUBMITTED"):
        req.status = "QUOTES_RECEIVED"

    await log_audit(db, "supplier_portal", "SUBMIT_QUOTE", "quote", display_id,
                    new_value={"supplier_id": body.supplier_id, "total_price": body.total_price})
    await db.commit()
    await db.refresh(quote)
    return {"message": "Quote submitted successfully", "quote_id": display_id}


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SupplierQuote).where(SupplierQuote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(404, "Quote not found")
    return quote


@router.get("/compare/{requirement_id}")
async def compare_quotes(
    requirement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare and score all quotes for a requirement."""
    quotes_result = await db.execute(
        select(SupplierQuote).where(SupplierQuote.requirement_id == requirement_id)
    )
    quotes = quotes_result.scalars().all()
    if not quotes:
        return {"message": "No quotes found", "scores": []}

    # Build scoring input
    scoring_input = []
    for q in quotes:
        supplier = (await db.execute(
            select(Supplier).where(Supplier.id == q.supplier_id)
        )).scalar_one_or_none()

        scoring_input.append({
            "supplier_id": q.supplier_id,
            "supplier_name": supplier.company_name if supplier else "Unknown",
            "quote_id": q.id,
            "display_id": q.display_id,
            "unit_price": q.unit_price,
            "total_price": q.total_price,
            "quantity": q.quantity,
            "lead_time_days": q.lead_time_days or 30,
            "availability": q.availability,
            "payment_terms": q.payment_terms,
            "warranty": q.warranty,
            "quality_score": supplier.quality_score if supplier else 50,
            "delivery_score": supplier.delivery_score if supplier else 50,
            "risk_score": supplier.risk_score if supplier else 50,
            "historical_performance": (supplier.quality_score + supplier.delivery_score) / 2 if supplier else 50,
        })

    scored = score_suppliers(scoring_input)
    results = []
    for s in scored:
        explanation = generate_explanation(s)
        results.append({
            **s.to_dict(),
            "explanation": explanation,
            "quote_display_id": next((si["display_id"] for si in scoring_input if si["supplier_id"] == s.supplier_id), None),
        })

    await log_audit(db, current_user.username, "COMPARE_QUOTES", "requirement",
                    str(requirement_id),
                    new_value={"quote_count": len(quotes), "recommended": results[0]["supplier_name"] if results else None})
    await db.commit()

    return {"requirement_id": requirement_id, "quote_count": len(quotes), "scores": results}
