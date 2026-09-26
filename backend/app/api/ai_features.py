"""
AI API – AI-assisted features for the SCM Procurement Control Tower.

Endpoints:
  POST /ai/extract-quote          – PDF/text → structured quote
  POST /ai/explain-scores         – Generate human-readable score explanation
  POST /ai/draft-negotiation      – Draft negotiation email (requires user approval)
  POST /ai/summarize-email        – Summarize supplier email/message
  POST /ai/explain-inventory-risk – Plain-language inventory risk explanation
  POST /ai/daily-brief            – Generate daily procurement brief
  GET  /ai/status                 – AI provider status
  GET  /ai/assistant              – Natural language procurement Q&A
"""

import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.requirement import Requirement
from app.models.supplier import Supplier
from app.models.supplier_quote import SupplierQuote
from app.models.approval import Approval
from app.models.inventory import InventoryItem
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.purchase_order import PurchaseOrder
from app.services.ai_service import ai_service, ExtractedQuote
from app.services.audit_service import log_audit
from app.services.inventory_service import calculate_inventory_analysis

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────

class ExplainScoresRequest(BaseModel):
    scored_suppliers: list[dict]
    requirement_id: Optional[int] = None
    material_name: Optional[str] = None
    budget: Optional[float] = None

class DraftNegotiationRequest(BaseModel):
    supplier_name: str
    requirement_id: str
    material: str
    quoted_price: float
    target_budget: float
    desired_delivery_days: int = 14
    preferred_payment_terms: str = "NET 30"
    additional_context: str = ""

class SummarizeEmailRequest(BaseModel):
    text: str
    context: str = ""

class ExplainInventoryRequest(BaseModel):
    material_code: str

class AssistantRequest(BaseModel):
    question: str


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.get("/status")
async def ai_status(current_user: User = Depends(get_current_user)):
    """Return the current AI provider configuration status."""
    return {
        "provider": ai_service.provider,
        "available": ai_service.is_available,
        "model": ai_service.model,
        "mode": "live" if ai_service.is_available else "mock/fallback",
        "message": (
            f"Connected to {ai_service.provider} ({ai_service.model})"
            if ai_service.is_available
            else "Running in deterministic fallback mode. Set AI_PROVIDER and AI_API_KEY in .env to enable AI."
        ),
    }


@router.post("/extract-quote")
async def extract_quote_from_document(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    requirement_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract structured quote fields from an uploaded document (PDF/text) or raw text.

    The AI extracts fields. Required fields are validated.
    If fields are missing, status = NEEDS_REVIEW (not silently filled).
    """
    document_text = ""

    if file:
        content = await file.read()
        # PDF handling: try pdfplumber, fallback to raw text
        try:
            import pdfplumber  # type: ignore
            import io
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                document_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ImportError:
            # pdfplumber not installed — treat as plain text
            try:
                document_text = content.decode("utf-8", errors="replace")
            except Exception:
                document_text = str(content)[:3000]
        except Exception:
            try:
                document_text = content.decode("utf-8", errors="replace")
            except Exception:
                document_text = ""

    elif text:
        document_text = text
    else:
        raise HTTPException(400, "Provide either a file upload or text parameter")

    if not document_text.strip():
        raise HTTPException(400, "Document appears to be empty")

    # Get requirement context if provided
    context = {}
    if requirement_id:
        req = (await db.execute(select(Requirement).where(Requirement.id == requirement_id))).scalar_one_or_none()
        if req:
            context = {
                "material_code": req.material_code,
                "material_name": req.material_name,
                "quantity": req.quantity,
                "budget": req.budget,
            }

    extracted = await ai_service.extract_document(document_text, context)

    await log_audit(
        db, current_user.username, "AI_EXTRACT_QUOTE",
        "quote_extraction", f"req_{requirement_id or 'unknown'}",
        new_value={
            "provider": ai_service.provider,
            "confidence": extracted.confidence,
            "needs_review": extracted.needs_review,
            "missing_fields": extracted.missing_fields,
        }
    )
    await db.commit()

    return {
        "extracted": extracted.to_dict(),
        "status": "NEEDS_REVIEW" if extracted.needs_review else "READY",
        "ai_provider": ai_service.provider if ai_service.is_available else "mock",
        "confidence": extracted.confidence,
        "missing_fields": extracted.missing_fields,
        "message": (
            f"Extraction complete. {len(extracted.missing_fields)} required fields missing — review before saving."
            if extracted.missing_fields
            else "Extraction complete. All required fields found."
        ),
    }


@router.post("/explain-scores")
async def explain_supplier_scores(
    body: ExplainScoresRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a human-readable explanation of pre-computed supplier scores.
    The AI receives scores from the deterministic engine — it does NOT recalculate.
    """
    requirement_context = {}
    if body.requirement_id:
        req = (await db.execute(select(Requirement).where(Requirement.id == body.requirement_id))).scalar_one_or_none()
        if req:
            requirement_context = {
                "requirement_id": req.display_id,
                "material": req.material_name,
                "quantity": req.quantity,
                "budget": req.budget,
                "required_by": req.required_by_date.isoformat() if req.required_by_date else None,
            }

    if body.material_name:
        requirement_context["material"] = body.material_name
    if body.budget:
        requirement_context["budget"] = body.budget

    explanation = await ai_service.generate_explanation(body.scored_suppliers, requirement_context)

    return {
        "explanation": explanation,
        "scored_count": len(body.scored_suppliers),
        "ai_provider": ai_service.provider if ai_service.is_available else "mock",
        "disclaimer": "Score rankings are determined by the deterministic scoring engine. AI provides explanation only.",
    }


@router.post("/draft-negotiation")
async def draft_negotiation_email(
    body: DraftNegotiationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Draft a supplier negotiation email.
    Returns a DRAFT — user must explicitly approve before sending.
    """
    draft = await ai_service.draft_email(
        supplier_name=body.supplier_name,
        requirement_id=body.requirement_id,
        material=body.material,
        quoted_price=body.quoted_price,
        target_budget=body.target_budget,
        desired_delivery_days=body.desired_delivery_days,
        preferred_payment_terms=body.preferred_payment_terms,
        additional_context=body.additional_context,
    )

    await log_audit(
        db, current_user.username, "AI_DRAFT_EMAIL",
        "negotiation", body.requirement_id,
        new_value={"supplier": body.supplier_name, "ai_provider": ai_service.provider}
    )
    await db.commit()

    return draft


@router.post("/summarize-email")
async def summarize_supplier_email(
    body: SummarizeEmailRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Summarize a supplier email/message into structured procurement-relevant fields.
    """
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty")

    summary = await ai_service.summarize_text(body.text, body.context)

    return {
        "summary": summary.to_dict(),
        "ai_provider": ai_service.provider if ai_service.is_available else "mock",
    }


@router.post("/explain-inventory-risk")
async def explain_inventory_risk(
    body: ExplainInventoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI-powered plain-language explanation of inventory risk.
    Calculation is deterministic; AI only explains it.
    """
    item = (await db.execute(
        select(InventoryItem).where(InventoryItem.material_code == body.material_code)
    )).scalar_one_or_none()

    if not item:
        raise HTTPException(404, f"Inventory item not found: {body.material_code}")

    # Get open PO quantity
    open_po_qty = (await db.execute(
        select(func.sum(PurchaseOrder.quantity)).where(
            PurchaseOrder.material_code == item.material_code,
            PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED", "PARTIALLY_RECEIVED"])
        )
    )).scalar() or 0.0

    analysis = calculate_inventory_analysis(
        material_code=item.material_code,
        material_name=item.material_name,
        quantity_on_hand=item.quantity_on_hand,
        reserved_quantity=item.reserved_quantity,
        safety_stock=item.safety_stock,
        minimum_stock=item.minimum_stock,
        reorder_level=item.reorder_level,
        average_daily_consumption=item.average_daily_consumption,
        lead_time_days=item.lead_time_days,
        open_po_quantity=float(open_po_qty),
    )

    explanation = await ai_service.explain_inventory_risk(analysis.to_dict())

    return {
        "material_code": item.material_code,
        "material_name": item.material_name,
        "analysis": analysis.to_dict(),
        "ai_explanation": explanation,
        "ai_provider": ai_service.provider if ai_service.is_available else "mock",
        "disclaimer": "Risk calculations are deterministic. AI provides explanation only.",
    }


@router.post("/daily-brief")
async def generate_daily_brief(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate the daily AI procurement brief.
    All data is fetched from deterministic system first; AI only summarizes.
    """
    from datetime import timedelta
    now = datetime.now(timezone.utc)

    # ── Collect verified data ──────────────────────────────
    pending_approvals = (await db.execute(
        select(func.count()).select_from(Approval).where(Approval.status == "PENDING")
    )).scalar() or 0

    open_requirements = (await db.execute(
        select(func.count()).select_from(Requirement).where(
            Requirement.status.in_(["SUBMITTED", "RFQ_IN_PROGRESS", "QUOTES_RECEIVED", "APPROVAL_PENDING"])
        )
    )).scalar() or 0

    # Stock risks
    items = (await db.execute(select(InventoryItem))).scalars().all()
    stock_risks = []
    for item in items:
        avail = item.quantity_on_hand - item.reserved_quantity
        if avail <= item.safety_stock:
            stock_risks.append({
                "material": item.material_name,
                "code": item.material_code,
                "available": avail,
                "safety_stock": item.safety_stock,
                "risk": "STOCKOUT" if avail <= 0 else "CRITICAL",
            })

    # Payment due soon
    overdue_invoices = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date <= now,
        )
    )).scalars().all()

    due_3days = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date > now,
            Invoice.due_date <= now + timedelta(days=3),
        )
    )).scalars().all()

    due_7days = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date > now + timedelta(days=3),
            Invoice.due_date <= now + timedelta(days=7),
        )
    )).scalars().all()

    # Invoice mismatches
    discrepancies = (await db.execute(
        select(func.count()).select_from(Invoice).where(Invoice.status == "DISCREPANCY")
    )).scalar() or 0

    # High-risk suppliers
    high_risk_suppliers = (await db.execute(
        select(Supplier).where(Supplier.risk_score >= 60).limit(5)
    )).scalars().all()

    # Assemble verified data dict for AI
    system_data = {
        "date": now.strftime("%Y-%m-%d"),
        "pending_approvals": pending_approvals,
        "open_requirements": open_requirements,
        "stock_risk_count": len(stock_risks),
        "stock_risks": stock_risks[:3],
        "overdue_invoices_count": len(overdue_invoices),
        "overdue_invoice_ids": [i.display_id for i in overdue_invoices],
        "due_3_days_count": len(due_3days),
        "due_7_days_count": len(due_7days),
        "invoice_discrepancies": discrepancies,
        "high_risk_supplier_count": len(high_risk_suppliers),
        "high_risk_suppliers": [s.company_name for s in high_risk_suppliers],
    }

    # AI summarizes — does NOT invent
    ai_result = await ai_service.generate_daily_summary(system_data)

    return {
        **ai_result,
        "system_data": system_data,
        "generated_at": now.isoformat(),
    }


@router.post("/assistant")
async def procurement_assistant(
    body: AssistantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Natural language procurement assistant.
    Answers questions using verified application data — NOT arbitrary DB access.
    Questions are matched to specific data-fetch functions.
    """
    question = body.question.lower().strip()
    now = datetime.now(timezone.utc)

    # ── Intent routing (no LangGraph/tool loops — clean interfaces) ──
    from datetime import timedelta

    if any(k in question for k in ["critical", "issue", "problem", "attention", "today"]):
        # Fetch attention items
        approvals = (await db.execute(
            select(Approval).where(Approval.status == "PENDING").limit(5)
        )).scalars().all()
        inv_risks = []
        items = (await db.execute(select(InventoryItem))).scalars().all()
        for item in items:
            if item.quantity_on_hand - item.reserved_quantity <= item.safety_stock:
                inv_risks.append(item.material_name)

        overdue = (await db.execute(
            select(Invoice).where(Invoice.status.in_(["VALIDATED", "APPROVED"]), Invoice.due_date <= now)
        )).scalars().all()

        data = {
            "pending_approvals": len(approvals),
            "stock_risks": inv_risks,
            "overdue_invoices": [i.display_id for i in overdue],
        }
        answer = f"**Today's Critical Issues:**\n\n"
        if data["pending_approvals"]:
            answer += f"• **{data['pending_approvals']} approval(s) pending** — action required\n"
        if data["stock_risks"]:
            answer += f"• **{len(data['stock_risks'])} stock risk(s):** {', '.join(data['stock_risks'][:3])}\n"
        if data["overdue_invoices"]:
            answer += f"• **{len(data['overdue_invoices'])} overdue invoice(s):** {', '.join(data['overdue_invoices'][:3])}\n"
        if not any([data["pending_approvals"], data["stock_risks"], data["overdue_invoices"]]):
            answer = "✅ No critical issues found today."

    elif any(k in question for k in ["approval", "waiting", "pending", "review"]):
        approvals = (await db.execute(
            select(Approval).where(Approval.status == "PENDING")
        )).scalars().all()
        answer = f"**{len(approvals)} Pending Approval(s):**\n"
        for a in approvals[:5]:
            answer += f"• APR #{a.id} — {a.entity_type} #{a.entity_id} (Level {a.approval_level})\n"

    elif any(k in question for k in ["invoice", "due", "payment", "7 days"]):
        due = (await db.execute(
            select(Invoice).where(
                Invoice.status.in_(["VALIDATED", "APPROVED"]),
                Invoice.due_date <= now + timedelta(days=7)
            )
        )).scalars().all()
        answer = f"**{len(due)} Invoice(s) due within 7 days:**\n"
        for inv in due[:5]:
            days_left = (inv.due_date - now).days if inv.due_date else "?"
            answer += f"• {inv.display_id} — ₹{inv.total_amount:,.0f} — {'overdue' if days_left < 0 else str(days_left) + ' days'}\n"

    elif any(k in question for k in ["stockout", "stock risk", "inventory", "material risk"]):
        items = (await db.execute(select(InventoryItem))).scalars().all()
        risks = [(i.material_name, i.material_code, i.quantity_on_hand - i.reserved_quantity, i.safety_stock)
                 for i in items if i.quantity_on_hand - i.reserved_quantity <= i.safety_stock]
        answer = f"**{len(risks)} Material(s) at Stock Risk:**\n"
        for name, code, avail, safety in risks[:5]:
            answer += f"• {name} ({code}) — Available: {avail:.0f}, Safety: {safety:.0f}\n"

    elif any(k in question for k in ["requirement", "req-", "req#"]):
        reqs = (await db.execute(
            select(Requirement).where(
                Requirement.status.notin_(["COMPLETED", "CANCELLED"])
            ).limit(10)
        )).scalars().all()
        answer = f"**{len(reqs)} Open Requirement(s):**\n"
        for r in reqs[:5]:
            answer += f"• {r.display_id} — {r.material_name} × {r.quantity} {r.unit} [{r.status}]\n"

    elif any(k in question for k in ["supplier", "score", "recommend"]):
        # Extract requirement ID if mentioned
        import re
        req_match = re.search(r'req[-#]?(\d+)', question)
        if req_match:
            req_id = req_match.group(1)
            reqs = (await db.execute(
                select(Requirement).where(Requirement.display_id.ilike(f"%{req_id}%"))
            )).scalars().all()
            if reqs:
                quotes = (await db.execute(
                    select(SupplierQuote).where(SupplierQuote.requirement_id == reqs[0].id).limit(5)
                )).scalars().all()
                answer = f"**Quotes for {reqs[0].display_id} ({reqs[0].material_name}):**\n"
                for q in quotes:
                    sup = (await db.execute(select(Supplier).where(Supplier.id == q.supplier_id))).scalar_one_or_none()
                    answer += f"• {sup.company_name if sup else 'Unknown'} — ₹{q.unit_price:,.2f}/unit, Lead: {q.lead_time_days}d, Terms: {q.payment_terms}\n"
            else:
                answer = f"No requirement found matching '{req_id}'."
        else:
            suppliers = (await db.execute(select(Supplier).limit(10))).scalars().all()
            answer = f"**{len(suppliers)} Suppliers in system:**\n"
            for s in suppliers[:5]:
                answer += f"• {s.company_name} — Quality: {s.quality_score}, Delivery: {s.delivery_score}, Risk: {s.risk_score}\n"

    elif any(k in question for k in ["po", "purchase order", "what happened"]):
        import re
        po_match = re.search(r'po[-#]?(\d+)', question, re.IGNORECASE)
        if po_match:
            po_num = po_match.group(0).upper().replace("#", "-").replace("PO", "PO-")
            pos = (await db.execute(
                select(PurchaseOrder).where(PurchaseOrder.display_id.ilike(f"%{po_num}%"))
            )).scalars().all()
            if pos:
                po = pos[0]
                answer = f"**{po.display_id}:** {po.material_name} × {po.quantity}\n"
                answer += f"Status: {po.status}\nSAP: {po.sap_po_number or 'Not synced'}\nAmount: ₹{po.total_amount:,.0f}"
            else:
                answer = f"Purchase order matching '{po_num}' not found."
        else:
            pos = (await db.execute(select(PurchaseOrder).limit(5))).scalars().all()
            answer = f"**Recent Purchase Orders:**\n"
            for po in pos:
                answer += f"• {po.display_id} — {po.material_name} [{po.status}]\n"
    else:
        # Fallback — generate with AI
        context_data = {
            "pending_approvals": (await db.execute(select(func.count()).select_from(Approval).where(Approval.status == "PENDING"))).scalar() or 0,
            "open_requirements": (await db.execute(select(func.count()).select_from(Requirement).where(Requirement.status.notin_(["COMPLETED", "CANCELLED"])))).scalar() or 0,
        }
        system_prompt = "You are a procurement assistant. Answer questions about procurement using the provided data context. Be concise and factual."
        user_prompt = f"Data context: {json.dumps(context_data)}\n\nQuestion: {body.question}"
        answer = await ai_service._call_ai(system_prompt, user_prompt)

    return {
        "question": body.question,
        "answer": answer,
        "data_source": "verified_system_data",
        "ai_provider": ai_service.provider if ai_service.is_available else "mock",
        "timestamp": now.isoformat(),
    }
