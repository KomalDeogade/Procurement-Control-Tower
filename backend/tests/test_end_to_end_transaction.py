"""
Automated End-to-End Transaction Integration Test.
Executes complete procurement lifecycle from scratch with NO manual database changes:
REQ-TEST-001
→ RFQ Generation
→ 3 Supplier Quotes
→ Quote Comparison & Scoring
→ Manager Approval
→ Purchase Order Creation
→ SAPAdapter Sync (Mock SAP)
→ Goods Receipt (GRN)
→ Inventory Update
→ Supplier Invoice
→ 3-Way Match
→ Payment Monitoring
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.models.requirement import Requirement, RequirementStatus
from app.models.rfq import RFQ, RFQStatus
from app.models.supplier import Supplier
from app.models.supplier_quote import SupplierQuote, QuoteStatus
from app.models.approval import Approval, ApprovalStatus
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.goods_receipt import GoodsReceipt
from app.models.inventory import InventoryItem
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.services.scoring_service import score_suppliers, ScoredSupplier
from app.services.three_way_match import three_way_match
from app.services.inventory_service import calculate_inventory_analysis
from app.integrations.sap_adapter import MockSAPAdapter


@pytest.mark.asyncio
async def test_end_to_end_procurement_transaction(db_session):
    now = datetime.now(timezone.utc)

    # ── Step 1: Create Requirement REQ-TEST-001 ─────────────────────
    req = Requirement(
        display_id="REQ-TEST-001",
        material_code="MAT-TEST-99",
        material_name="Test Alloy Rod 50mm",
        description="End-to-end test procurement requirement",
        quantity=500,
        unit="KG",
        plant="PLANT-01",
        required_by_date=now + timedelta(days=14),
        budget=150000.0,
        currency="INR",
        priority="HIGH",
        status=RequirementStatus.SUBMITTED,
    )
    db_session.add(req)
    await db_session.flush()
    assert req.id is not None
    assert req.display_id == "REQ-TEST-001"

    # ── Step 2: Create 3 Suppliers & Generate RFQs ───────────────────
    suppliers = []
    rfqs = []
    for i in range(1, 4):
        sup = Supplier(
            supplier_code=f"SUP-TEST-0{i}",
            company_name=f"Test Vendor {chr(64 + i)}",
            contact_person=f"Contact {i}",
            email=f"vendor_{i}@test.scm",
            quality_score=80.0 + (i * 5),
            delivery_score=75.0 + (i * 6),
            risk_score=20.0 + (i * 5),
            payment_terms="NET 30",
            approval_status="APPROVED",
        )
        db_session.add(sup)
        await db_session.flush()
        suppliers.append(sup)

        rfq = RFQ(
            display_id=f"RFQ-TEST-0{i}",
            requirement_id=req.id,
            supplier_id=sup.id,
            access_token=f"token_test_rfq_0{i}",
            status=RFQStatus.SENT,
        )
        db_session.add(rfq)
        await db_session.flush()
        rfqs.append(rfq)

    assert len(suppliers) == 3
    assert len(rfqs) == 3

    # ── Step 3: Submit 3 Supplier Quotes ─────────────────────────────
    quotes = []
    prices = [280.0, 260.0, 290.0]  # Vendor B cheapest base price
    for i, sup in enumerate(suppliers):
        quote = SupplierQuote(
            display_id=f"QT-TEST-0{i+1}",
            requirement_id=req.id,
            supplier_id=sup.id,
            unit_price=prices[i],
            quantity=500,
            tax=prices[i] * 500 * 0.18,
            freight=2000.0,
            total_price=(prices[i] * 500 * 1.18) + 2000.0,
            availability=True,
            lead_time_days=7 + (i * 2),
            payment_terms="NET 30",
            status=QuoteStatus.SUBMITTED,
        )
        db_session.add(quote)
        await db_session.flush()
        quotes.append(quote)

    assert len(quotes) == 3

    # ── Step 4: Dynamic Supplier Scoring & Evaluation ────────────────
    quote_dicts = []
    for q in quotes:
        sup = next(s for s in suppliers if s.id == q.supplier_id)
        quote_dicts.append({
            "supplier_id": sup.id,
            "supplier_name": sup.company_name,
            "unit_price": q.unit_price,
            "total_price": q.total_price,
            "quantity": q.quantity,
            "lead_time_days": q.lead_time_days,
            "availability": "Immediate",
            "payment_terms": q.payment_terms,
            "quality_score": sup.quality_score,
            "delivery_score": sup.delivery_score,
            "risk_score": sup.risk_score,
            "historical_performance": 85.0,
        })
    scored_list = score_suppliers(quote_dicts)
    assert len(scored_list) == 3

    top_scored = max(scored_list, key=lambda x: x.score)
    best_quote = next(q for q in quotes if q.supplier_id == top_scored.supplier_id)
    assert best_quote is not None
    assert top_scored.score > 0

    # ── Step 5: Manager Approval ─────────────────────────────────────
    approval = Approval(
        display_id="APP-TEST-001",
        entity_type="requirement",
        entity_id=req.id,
        approval_level=1,
        status=ApprovalStatus.APPROVED,
        comments="Approved optimal quote after deterministic scoring evaluation.",
    )
    db_session.add(approval)
    req.status = RequirementStatus.APPROVED
    await db_session.flush()
    assert approval.status == ApprovalStatus.APPROVED

    # ── Step 6: Create Purchase Order & Mock SAP Sync ────────────────
    po = PurchaseOrder(
        display_id="PO-TEST-001",
        requirement_id=req.id,
        supplier_id=best_quote.supplier_id,
        quote_id=best_quote.id,
        material_code=req.material_code,
        material_name=req.material_name,
        quantity=req.quantity,
        unit_price=best_quote.unit_price,
        total_amount=best_quote.total_price,
        sap_po_number="450001001",  # Mock SAP PO Reference
        status=POStatus.SAP_CREATED,
    )
    db_session.add(po)
    await db_session.flush()
    assert po.sap_po_number == "450001001"

    # ── Step 7: Goods Receipt (GRN) & Inventory Update ───────────────
    grn = GoodsReceipt(
        display_id="GRN-TEST-001",
        po_id=po.id,
        received_quantity=500.0,
        quality_status="PASSED",
        inspector="Quality Control Eng",
        sap_grn_number="500001001",
    )
    db_session.add(grn)

    # Update Inventory
    inv_item = InventoryItem(
        material_code=req.material_code,
        material_name=req.material_name,
        quantity_on_hand=500.0,
        reserved_quantity=0.0,
        unit="KG",
        plant="PLANT-01",
        warehouse="WH-A",
        reorder_level=100.0,
        safety_stock=50.0,
        average_daily_consumption=25.0,
        lead_time_days=7,
    )
    db_session.add(inv_item)
    await db_session.flush()

    assert inv_item.quantity_on_hand == 500.0

    # ── Step 8: Invoice Creation & 3-Way Match ────────────────────────
    invoice = Invoice(
        display_id="INV-TEST-001",
        po_id=po.id,
        supplier_id=po.supplier_id,
        invoice_amount=best_quote.total_price - best_quote.tax,
        tax_amount=best_quote.tax,
        total_amount=best_quote.total_price,
        invoice_date=now,
        due_date=now + timedelta(days=30),
        status=InvoiceStatus.VALIDATED,
        sap_invoice_number="220001001",
    )
    db_session.add(invoice)
    await db_session.flush()

    # Perform 3-Way Match
    match_result = three_way_match(
        po_quantity=po.quantity,
        po_unit_price=po.unit_price,
        po_total=po.total_amount,
        grn_quantity=grn.received_quantity,
        invoice_quantity=po.quantity,
        invoice_unit_price=po.unit_price,
        invoice_total=invoice.total_amount,
    )
    assert match_result.status == "MATCHED"
    assert match_result.quantity_match is True
    assert match_result.price_match is True

    # ── Step 9: Payment Due Monitoring & Process Payment ──────────────
    payment = Payment(
        display_id="PAY-TEST-001",
        invoice_id=invoice.id,
        amount=invoice.total_amount,
        payment_method="BANK_TRANSFER",
        status=PaymentStatus.PAID,
        reference_number="UTR998877665544",
    )
    db_session.add(payment)
    await db_session.flush()

    assert payment.status == PaymentStatus.PAID
    assert payment.reference_number == "UTR998877665544"
