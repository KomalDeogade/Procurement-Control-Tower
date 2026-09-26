"""
Demo Mode API – One-click demo scenario setup.

Creates or identifies the XLR-500 demo scenario with:
- REQ-DEMO: Industrial Lubricant XLR-500, 5000L, ₹80L budget
- Three suppliers: Vendor A (reliable), Vendor B (cheap/delayed), Vendor C (expensive)
- Exception scenario: Vendor B cheaper but delayed, invoice mismatch, payment due
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.requirement import Requirement, RequirementStatus
from app.models.supplier import Supplier
from app.models.rfq import RFQ, RFQStatus
from app.models.supplier_quote import SupplierQuote, QuoteStatus
from app.models.approval import Approval, ApprovalStatus
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.services.audit_service import log_audit

router = APIRouter()

DEMO_MATERIAL_CODE = "XLR-500-DEMO"
DEMO_REQ_DISPLAY = "REQ-DEMO"


async def _get_or_create_demo_supplier(db: AsyncSession, code: str, name: str, quality: float, delivery: float, risk: float, email: str, payment_terms: str) -> Supplier:
    existing = (await db.execute(
        select(Supplier).where(Supplier.supplier_code == code)
    )).scalar_one_or_none()
    if existing:
        return existing
    sup = Supplier(
        supplier_code=code,
        company_name=name,
        contact_person="Demo Contact",
        email=email,
        quality_score=quality,
        delivery_score=delivery,
        risk_score=risk,
        payment_terms=payment_terms,
        approval_status="APPROVED",
        category="Industrial Chemicals",
        location="Mumbai, India",
    )
    db.add(sup)
    await db.flush()
    return sup


@router.post("/reset")
async def reset_demo(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset and initialize the XLR-500 demo scenario.
    Safe to run multiple times — skips already-created items.
    Returns step-by-step status of demo setup.
    """
    now = datetime.now(timezone.utc)
    steps = []

    # ── Step 1: Demo Suppliers ─────────────────────────────────
    vendor_a = await _get_or_create_demo_supplier(
        db, "DEMO-VENDOR-A", "Vendor A (Alpha Lubricants)",
        quality=92.0, delivery=88.0, risk=18.0,
        email="vendor-a@demo.scm", payment_terms="NET 30"
    )
    vendor_b = await _get_or_create_demo_supplier(
        db, "DEMO-VENDOR-B", "Vendor B (Beta Industrial)",
        quality=72.0, delivery=55.0, risk=48.0,  # ← delayed delivery (low score)
        email="vendor-b@demo.scm", payment_terms="NET 45"
    )
    vendor_c = await _get_or_create_demo_supplier(
        db, "DEMO-VENDOR-C", "Vendor C (Gamma Chemicals)",
        quality=65.0, delivery=70.0, risk=35.0,
        email="vendor-c@demo.scm", payment_terms="ADVANCE"
    )
    steps.append({"step": 1, "name": "Demo Suppliers", "status": "OK",
                  "detail": f"Vendors A ({vendor_a.id}), B ({vendor_b.id}), C ({vendor_c.id})"})

    # ── Step 2: Requirement ────────────────────────────────────
    existing_req = (await db.execute(
        select(Requirement).where(Requirement.display_id == DEMO_REQ_DISPLAY)
    )).scalar_one_or_none()

    if existing_req:
        req = existing_req
        steps.append({"step": 2, "name": "Requirement", "status": "EXISTING", "detail": req.display_id})
    else:
        req = Requirement(
            display_id=DEMO_REQ_DISPLAY,
            material_code=DEMO_MATERIAL_CODE,
            material_name="Industrial Lubricant XLR-500",
            description="High-performance industrial lubricant for heavy machinery. Demo scenario.",
            quantity=5000.0,
            unit="L",
            plant="Mumbai Plant 1",
            required_by_date=now + timedelta(days=30),
            budget=8_000_000.0,
            currency="INR",
            priority="HIGH",
            status=RequirementStatus.QUOTES_RECEIVED,
        )
        db.add(req)
        await db.flush()
        steps.append({"step": 2, "name": "Requirement", "status": "CREATED", "detail": DEMO_REQ_DISPLAY})

    # ── Step 3: RFQs ──────────────────────────────────────────
    for sup, idx in [(vendor_a, 1), (vendor_b, 2), (vendor_c, 3)]:
        existing_rfq = (await db.execute(
            select(RFQ).where(RFQ.requirement_id == req.id, RFQ.supplier_id == sup.id)
        )).scalar_one_or_none()
        if not existing_rfq:
            all_rfqs = (await db.execute(select(RFQ))).scalars().all()
            rfq = RFQ(
                display_id=f"RFQ-DEMO-{idx}",
                requirement_id=req.id,
                supplier_id=sup.id,
                status=RFQStatus.RESPONDED,
                response_deadline=now + timedelta(days=7),
                notes=f"Demo RFQ for {sup.company_name}",
            )
            db.add(rfq)

    steps.append({"step": 3, "name": "RFQs", "status": "OK", "detail": "3 RFQs sent to Vendor A, B, C"})

    # ── Step 4: Quotes ─────────────────────────────────────────
    # Vendor A: reliable, slightly above budget
    # Vendor B: cheapest but 45-day delivery (EXCEPTION scenario)
    # Vendor C: expensive, advance payment required (EXCEPTION)
    quote_defs = [
        (vendor_a, 1680.0, 14, "NET 30", "In Stock", "12 months"),   # ← best overall
        (vendor_b, 1520.0, 45, "NET 45", "Within 6 weeks", "6 months"),  # ← cheap but delayed
        (vendor_c, 1950.0, 21, "ADVANCE", "Within 3 weeks", "24 months"),  # ← expensive + advance
    ]

    all_quotes = (await db.execute(select(SupplierQuote))).scalars().all()
    existing_demo_quotes = [q for q in all_quotes if q.requirement_id == req.id]
    demo_quote_suppliers = {q.supplier_id for q in existing_demo_quotes}

    created_quotes = []
    for idx, (sup, unit_price, lead_time, terms, avail, warranty) in enumerate(quote_defs, start=1):
        if sup.id in demo_quote_suppliers:
            existing_q = next((q for q in existing_demo_quotes if q.supplier_id == sup.id), None)
            created_quotes.append(existing_q)
            continue
        total = unit_price * 5000
        quote = SupplierQuote(
            display_id=f"QUOTE-DEMO-{idx}",
            requirement_id=req.id,
            supplier_id=sup.id,
            unit_price=unit_price,
            quantity=5000.0,
            tax=total * 0.18,
            freight=25000.0,
            total_price=total + (total * 0.18) + 25000,
            availability=avail,
            lead_time_days=lead_time,
            delivery_date=now + timedelta(days=lead_time),
            payment_terms=terms,
            warranty=warranty,
            service_details="Includes technical documentation and MSDS sheet",
            advantages=f"Demo advantage for Vendor {['A', 'B', 'C'][idx-1]}",
            status=QuoteStatus.SUBMITTED,
            submitted_at=now - timedelta(hours=2),
        )
        db.add(quote)
        await db.flush()
        created_quotes.append(quote)

    steps.append({"step": 4, "name": "Quotes",  "status": "OK",
                  "detail": "3 quotes: A=₹1,680/L (14d), B=₹1,520/L (45d DELAYED), C=₹1,950/L (ADVANCE)"})

    # ── Step 5: Demo Approval ──────────────────────────────────
    existing_apr = (await db.execute(
        select(Approval).where(Approval.entity_type == "requirement", Approval.entity_id == req.id)
    )).scalar_one_or_none()

    if not existing_apr:
        # Get manager user
        from app.models.user import User as UserModel
        manager = (await db.execute(
            select(UserModel).where(UserModel.username == "manager")
        )).scalar_one_or_none()

        if manager:
            approval = Approval(
                display_id="APR-DEMO-1",
                entity_type="requirement",
                entity_id=req.id,
                approver_id=manager.id,
                approval_level=1,
                status=ApprovalStatus.PENDING,
            )
            db.add(approval)
            steps.append({"step": 5, "name": "Approval", "status": "CREATED", "detail": "Pending manager approval — APR-DEMO-1"})
        else:
            steps.append({"step": 5, "name": "Approval", "status": "SKIPPED", "detail": "Manager user not found"})
    else:
        steps.append({"step": 5, "name": "Approval", "status": "EXISTING", "detail": existing_apr.display_id})

    # ── Step 6: Purchase Order (Vendor A selected) ─────────────
    existing_po = (await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.material_code == DEMO_MATERIAL_CODE,
            PurchaseOrder.supplier_id == vendor_a.id
        )
    )).scalar_one_or_none()

    if not existing_po:
        po = PurchaseOrder(
            display_id="PO-DEMO-1",
            requirement_id=req.id,
            supplier_id=vendor_a.id,
            material_code=DEMO_MATERIAL_CODE,
            material_name="Industrial Lubricant XLR-500",
            quantity=5000.0,
            unit_price=1680.0,
            total_amount=1680.0 * 5000,
            currency="INR",
            delivery_date=now + timedelta(days=14),
            payment_terms="NET 30",
            status=POStatus.SAP_CREATED,
            sap_po_number="SAP-PO-DEMO-001",
        )
        db.add(po)
        await db.flush()
        steps.append({"step": 6, "name": "Purchase Order", "status": "CREATED",
                      "detail": f"PO-DEMO-1 for Vendor A. SAP: SAP-PO-DEMO-001"})
    else:
        po = existing_po
        steps.append({"step": 6, "name": "Purchase Order", "status": "EXISTING", "detail": po.display_id})

    # ── Step 7: Invoice with EXCEPTION scenario ────────────────
    existing_inv = (await db.execute(
        select(Invoice).where(Invoice.po_id == po.id)
    )).scalar_one_or_none()

    if not existing_inv:
        # Intentional quantity mismatch: invoice for 4800L (PO was 5000L) → exception
        inv = Invoice(
            display_id="INV-DEMO-1",
            po_id=po.id,
            supplier_id=vendor_a.id,
            invoice_amount=1680.0 * 4800,  # EXCEPTION: 4800 not 5000
            tax_amount=1680.0 * 4800 * 0.18,
            total_amount=1680.0 * 4800 * 1.18,
            invoice_date=now - timedelta(days=2),
            due_date=now + timedelta(days=4),  # EXCEPTION: due in 4 days
            status=InvoiceStatus.DISCREPANCY,  # already failed 3-way match
            notes="DEMO: Invoice quantity 4800L vs PO 5000L — intentional exception",
        )
        db.add(inv)
        steps.append({"step": 7, "name": "Invoice (Exception)", "status": "CREATED",
                      "detail": "INV-DEMO-1: 4800L vs PO 5000L (DISCREPANCY), due in 4 days"})
    else:
        steps.append({"step": 7, "name": "Invoice", "status": "EXISTING", "detail": existing_inv.display_id})

    await log_audit(db, current_user.username, "DEMO_RESET", "demo", "XLR-500",
                    new_value={"steps": len(steps), "triggered_by": current_user.username})
    await db.commit()

    return {
        "status": "OK",
        "message": "Demo scenario ready. Navigate to the dashboard to see the XLR-500 workflow.",
        "scenario": {
            "requirement": DEMO_REQ_DISPLAY,
            "material": "Industrial Lubricant XLR-500",
            "quantity": "5,000 L",
            "budget": "₹80,00,000",
            "suppliers": ["Vendor A (Recommended)", "Vendor B (Cheaper, 45-day delay)", "Vendor C (Advance payment)"],
        },
        "exceptions_demonstrated": [
            "Vendor B: lower price but 45-day delivery exceeds requirement",
            "Vendor C: ADVANCE payment required — creates alert",
            "Invoice INV-DEMO-1: quantity mismatch (4800L vs 5000L) — 3-way match FAILED",
            "Invoice due in 4 days — payment watchdog alert",
        ],
        "steps": steps,
        "next_steps": [
            "1. Go to Dashboard — see 'Good Morning' brief with exceptions",
            "2. Go to Approvals — approve REQ-DEMO (Vendor A recommended)",
            "3. Go to Invoices — run 3-way match on INV-DEMO-1 to see discrepancy",
            "4. Go to Payments — see payment due alert for INV-DEMO-1",
            "5. Go to Quote Comparison — see why Vendor A scored higher than cheaper Vendor B",
        ],
    }


@router.get("/status")
async def demo_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if demo scenario is loaded."""
    req = (await db.execute(
        select(Requirement).where(Requirement.display_id == DEMO_REQ_DISPLAY)
    )).scalar_one_or_none()

    if not req:
        return {"loaded": False, "message": "Demo not loaded. POST /api/demo/reset to initialize."}

    quotes = (await db.execute(
        select(SupplierQuote).where(SupplierQuote.requirement_id == req.id)
    )).scalars().all()

    pos = (await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.material_code == DEMO_MATERIAL_CODE)
    )).scalars().all()

    invoices = (await db.execute(
        select(Invoice).where(Invoice.po_id.in_([p.id for p in pos]))
    )).scalars().all()

    return {
        "loaded": True,
        "requirement": {"id": req.display_id, "status": req.status},
        "quotes": len(quotes),
        "purchase_orders": len(pos),
        "invoices": len(invoices),
        "exceptions_active": any(i.status == "DISCREPANCY" for i in invoices),
    }
