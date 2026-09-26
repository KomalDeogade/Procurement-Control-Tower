"""
Reports API – Automated report generation and CSV/Excel export.

Does NOT depend on AI — reports are deterministic.
AI may add narrative summaries (optional enhancement).

Endpoints:
  GET  /reports/daily-summary           – Daily procurement summary
  GET  /reports/supplier-comparison     – Supplier comparison report
  GET  /reports/inventory-risk          – Inventory risk report
  GET  /reports/payment-due             – Payment due report
  GET  /reports/process-impact          – Process impact metrics
  GET  /reports/export/{report_type}    – Export as CSV
"""

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.requirement import Requirement
from app.models.supplier import Supplier
from app.models.supplier_quote import SupplierQuote
from app.models.approval import Approval
from app.models.purchase_order import PurchaseOrder
from app.models.inventory import InventoryItem
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.goods_receipt import GoodsReceipt
from app.models.audit_log import AuditLog
from app.services.payment_service import categorize_payment

router = APIRouter()


@router.get("/daily-summary")
async def daily_summary_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily procurement summary report — all data is deterministic."""
    now = datetime.now(timezone.utc)

    reqs = (await db.execute(select(Requirement))).scalars().all()
    suppliers = (await db.execute(select(Supplier))).scalars().all()
    quotes = (await db.execute(select(SupplierQuote))).scalars().all()
    approvals = (await db.execute(select(Approval))).scalars().all()
    pos = (await db.execute(select(PurchaseOrder))).scalars().all()
    invoices = (await db.execute(select(Invoice))).scalars().all()
    payments = (await db.execute(select(Payment))).scalars().all()
    items = (await db.execute(select(InventoryItem))).scalars().all()

    # Status breakdowns
    req_by_status = {}
    for r in reqs:
        req_by_status[r.status] = req_by_status.get(r.status, 0) + 1

    pending_approvals = [a for a in approvals if a.status == "PENDING"]
    overdue_invoices = [i for i in invoices if i.due_date and i.due_date <= now and i.status in ["VALIDATED", "APPROVED"]]

    stock_risk_items = []
    for item in items:
        avail = item.quantity_on_hand - item.reserved_quantity
        if avail <= item.safety_stock:
            stock_risk_items.append({
                "material_code": item.material_code,
                "material_name": item.material_name,
                "available": avail,
                "safety_stock": item.safety_stock,
                "risk": "STOCKOUT" if avail <= 0 else "CRITICAL",
            })

    total_po_value = sum(p.total_amount for p in pos)
    total_paid = sum(p.amount for p in payments if p.status == "COMPLETED")

    return {
        "report_type": "DAILY_SUMMARY",
        "generated_at": now.isoformat(),
        "summary": {
            "total_requirements": len(reqs),
            "requirements_by_status": req_by_status,
            "total_suppliers": len(suppliers),
            "active_quotes": len([q for q in quotes if q.status == "SUBMITTED"]),
            "pending_approvals": len(pending_approvals),
            "active_purchase_orders": len([p for p in pos if p.status not in ["COMPLETED", "CANCELLED"]]),
            "total_po_value": total_po_value,
            "total_paid_amount": total_paid,
            "overdue_invoices": len(overdue_invoices),
            "stock_risk_count": len(stock_risk_items),
        },
        "stock_risks": stock_risk_items,
        "pending_approval_details": [
            {"id": a.display_id, "entity_type": a.entity_type, "entity_id": a.entity_id, "level": a.approval_level}
            for a in pending_approvals
        ],
        "overdue_invoice_details": [
            {"id": i.display_id, "amount": i.total_amount, "due_date": i.due_date.strftime("%Y-%m-%d") if i.due_date else None}
            for i in overdue_invoices
        ],
    }


@router.get("/supplier-comparison")
async def supplier_comparison_report(
    requirement_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supplier comparison report — deterministic scoring data."""
    from app.services.scoring_service import score_suppliers, generate_explanation

    suppliers = (await db.execute(select(Supplier))).scalars().all()
    sup_map = {s.id: s for s in suppliers}

    # Get quotes
    q = select(SupplierQuote)
    if requirement_id:
        q = q.where(SupplierQuote.requirement_id == requirement_id)
    quotes = (await db.execute(q)).scalars().all()

    # Group by requirement
    by_req: dict[int, list] = {}
    for quote in quotes:
        by_req.setdefault(quote.requirement_id, []).append(quote)

    comparisons = []
    for req_id, req_quotes in by_req.items():
        req = (await db.execute(select(Requirement).where(Requirement.id == req_id))).scalar_one_or_none()
        scoring_input = []
        for q in req_quotes:
            sup = sup_map.get(q.supplier_id)
            if sup:
                scoring_input.append({
                    "supplier_id": q.supplier_id,
                    "supplier_name": sup.company_name,
                    "quote_id": q.id,
                    "display_id": q.display_id,
                    "unit_price": q.unit_price,
                    "total_price": q.total_price,
                    "quantity": q.quantity,
                    "lead_time_days": q.lead_time_days or 30,
                    "availability": q.availability,
                    "payment_terms": q.payment_terms,
                    "warranty": q.warranty,
                    "quality_score": sup.quality_score,
                    "delivery_score": sup.delivery_score,
                    "risk_score": sup.risk_score,
                    "historical_performance": (sup.quality_score + sup.delivery_score) / 2,
                })

        scored = score_suppliers(scoring_input)
        comparisons.append({
            "requirement_id": req.display_id if req else f"REQ#{req_id}",
            "material": req.material_name if req else "Unknown",
            "quote_count": len(req_quotes),
            "scores": [s.to_dict() for s in scored],
            "recommended": scored[0].supplier_name if scored else None,
        })

    return {
        "report_type": "SUPPLIER_COMPARISON",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_requirements": len(comparisons),
        "comparisons": comparisons,
        "scoring_weights": {
            "price": "30%", "delivery": "20%", "quality": "15%",
            "historical": "15%", "payment_terms": "10%",
            "availability": "5%", "risk": "5%"
        },
    }


@router.get("/inventory-risk")
async def inventory_risk_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inventory risk report — deterministic calculations only."""
    from app.services.inventory_service import calculate_inventory_analysis

    items = (await db.execute(select(InventoryItem))).scalars().all()
    results = []

    for item in items:
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
        results.append(analysis.to_dict())

    risk_summary = {
        "NORMAL": len([r for r in results if r["risk_status"] == "NORMAL"]),
        "LOW": len([r for r in results if r["risk_status"] == "LOW"]),
        "CRITICAL": len([r for r in results if r["risk_status"] == "CRITICAL"]),
        "STOCKOUT_RISK": len([r for r in results if r["risk_status"] == "STOCKOUT_RISK"]),
    }

    results.sort(key=lambda x: {"STOCKOUT_RISK": 0, "CRITICAL": 1, "LOW": 2, "NORMAL": 3}.get(x["risk_status"], 4))

    return {
        "report_type": "INVENTORY_RISK",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": risk_summary,
        "total_items": len(results),
        "items": results,
    }


@router.get("/payment-due")
async def payment_due_report(
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Payment due report for the next N days."""
    now = datetime.now(timezone.utc)

    invoices = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["SUBMITTED", "VALIDATED", "APPROVED", "PAYMENT_PENDING"]),
            Invoice.due_date <= now + timedelta(days=days_ahead),
        ).order_by(Invoice.due_date)
    )).scalars().all()

    suppliers = {s.id: s for s in (await db.execute(select(Supplier))).scalars().all()}
    pos = {p.id: p for p in (await db.execute(select(PurchaseOrder))).scalars().all()}

    items = []
    total_due = 0.0
    overdue_total = 0.0

    for inv in invoices:
        due = inv.due_date
        days_until = (due.date() - now.date()).days if due else 0
        cat = categorize_payment(days_until)
        sup = suppliers.get(inv.supplier_id)
        po = pos.get(inv.po_id)

        items.append({
            "invoice_id": inv.display_id,
            "supplier": sup.company_name if sup else f"SUP#{inv.supplier_id}",
            "po_number": po.display_id if po else f"PO#{inv.po_id}",
            "invoice_amount": inv.invoice_amount,
            "tax_amount": inv.tax_amount,
            "total_amount": inv.total_amount,
            "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else None,
            "due_date": due.strftime("%Y-%m-%d") if due else None,
            "days_until_due": days_until,
            "category": cat,
            "status": inv.status,
        })
        total_due += inv.total_amount
        if cat == "OVERDUE":
            overdue_total += inv.total_amount

    return {
        "report_type": "PAYMENT_DUE",
        "generated_at": now.isoformat(),
        "days_ahead": days_ahead,
        "total_invoices": len(items),
        "total_amount_due": total_due,
        "overdue_amount": overdue_total,
        "items": items,
    }


@router.get("/process-impact")
async def process_impact_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process impact metrics — calculated from actual demo workflow activity.
    No invented percentages.
    """
    now = datetime.now(timezone.utc)

    # Count actual events from audit log
    total_audit_events = (await db.execute(select(func.count()).select_from(AuditLog))).scalar() or 0

    automated_actions = (await db.execute(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.actor == "system"
        )
    )).scalar() or 0

    human_actions = total_audit_events - automated_actions

    ai_actions = (await db.execute(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action.like("AI_%")
        )
    )).scalar() or 0

    approvals_given = (await db.execute(
        select(func.count()).select_from(Approval).where(Approval.status.in_(["APPROVED", "REJECTED"]))
    )).scalar() or 0

    exceptions_raised = (await db.execute(
        select(func.count()).select_from(Invoice).where(Invoice.status == "DISCREPANCY")
    )).scalar() or 0

    total_requirements = (await db.execute(select(func.count()).select_from(Requirement))).scalar() or 0
    completed_pos = (await db.execute(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.status == "COMPLETED"))).scalar() or 0
    completed_payments = (await db.execute(select(func.count()).select_from(Payment).where(Payment.status == "COMPLETED"))).scalar() or 0

    # Quote comparison events
    compare_events = (await db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "COMPARE_QUOTES")
    )).scalar() or 0

    sap_syncs = (await db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "SAP_SYNC")
    )).scalar() or 0

    return {
        "report_type": "PROCESS_IMPACT",
        "generated_at": now.isoformat(),
        "workflow_counts": {
            "total_requirements_created": total_requirements,
            "purchase_orders_completed": completed_pos,
            "payments_processed": completed_payments,
            "supplier_comparisons_run": compare_events,
            "sap_syncs_completed": sap_syncs,
        },
        "automation_metrics": {
            "total_audit_events": total_audit_events,
            "human_actions": human_actions,
            "automated_system_actions": automated_actions,
            "ai_assisted_actions": ai_actions,
            "automation_rate_pct": round((automated_actions / total_audit_events * 100) if total_audit_events else 0, 1),
        },
        "quality_metrics": {
            "approvals_processed": approvals_given,
            "invoice_exceptions_caught": exceptions_raised,
            "manual_interventions_required": exceptions_raised + approvals_given,
        },
        "note": "All metrics calculated from actual system events. No values are invented or estimated.",
    }


@router.get("/export/{report_type}")
async def export_report_csv(
    report_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export reports as CSV files.
    Supported: daily-summary, inventory-risk, payment-due, supplier-comparison
    """
    now = datetime.now(timezone.utc)
    output = io.StringIO()

    if report_type == "inventory-risk":
        from app.services.inventory_service import calculate_inventory_analysis
        items = (await db.execute(select(InventoryItem))).scalars().all()
        writer = csv.DictWriter(output, fieldnames=[
            "material_code", "material_name", "quantity_on_hand", "available_stock",
            "safety_stock", "reorder_level", "risk_status", "stock_coverage_days",
            "projected_stockout_date", "recommended_reorder_qty", "average_daily_consumption", "lead_time_days"
        ])
        writer.writeheader()
        for item in items:
            open_po_qty = (await db.execute(
                select(func.sum(PurchaseOrder.quantity)).where(
                    PurchaseOrder.material_code == item.material_code,
                    PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED", "PARTIALLY_RECEIVED"])
                )
            )).scalar() or 0.0
            a = calculate_inventory_analysis(
                material_code=item.material_code, material_name=item.material_name,
                quantity_on_hand=item.quantity_on_hand, reserved_quantity=item.reserved_quantity,
                safety_stock=item.safety_stock, minimum_stock=item.minimum_stock,
                reorder_level=item.reorder_level, average_daily_consumption=item.average_daily_consumption,
                lead_time_days=item.lead_time_days, open_po_quantity=float(open_po_qty),
            )
            writer.writerow({
                "material_code": a.material_code, "material_name": a.material_name,
                "quantity_on_hand": a.quantity_on_hand, "available_stock": a.available_stock,
                "safety_stock": a.safety_stock, "reorder_level": a.reorder_level,
                "risk_status": a.risk_status, "stock_coverage_days": a.stock_coverage_days,
                "projected_stockout_date": a.projected_stockout_date,
                "recommended_reorder_qty": a.recommended_reorder_qty,
                "average_daily_consumption": a.average_daily_consumption,
                "lead_time_days": a.lead_time_days,
            })

    elif report_type == "payment-due":
        invoices = (await db.execute(
            select(Invoice).where(Invoice.status.in_(["SUBMITTED", "VALIDATED", "APPROVED"])).order_by(Invoice.due_date)
        )).scalars().all()
        suppliers = {s.id: s for s in (await db.execute(select(Supplier))).scalars().all()}
        writer = csv.DictWriter(output, fieldnames=[
            "invoice_id", "supplier", "total_amount", "invoice_date", "due_date", "days_until_due", "category", "status"
        ])
        writer.writeheader()
        for inv in invoices:
            due = inv.due_date
            days = (due.date() - now.date()).days if due else 0
            sup = suppliers.get(inv.supplier_id)
            writer.writerow({
                "invoice_id": inv.display_id,
                "supplier": sup.company_name if sup else f"SUP#{inv.supplier_id}",
                "total_amount": inv.total_amount,
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "",
                "due_date": due.strftime("%Y-%m-%d") if due else "",
                "days_until_due": days,
                "category": categorize_payment(days),
                "status": inv.status,
            })

    elif report_type == "daily-summary":
        reqs = (await db.execute(select(Requirement))).scalars().all()
        writer = csv.DictWriter(output, fieldnames=[
            "display_id", "material_name", "material_code", "quantity", "unit", "status", "priority", "budget", "created_at"
        ])
        writer.writeheader()
        for r in reqs:
            writer.writerow({
                "display_id": r.display_id, "material_name": r.material_name,
                "material_code": r.material_code, "quantity": r.quantity,
                "unit": r.unit, "status": r.status, "priority": r.priority,
                "budget": r.budget, "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            })

    elif report_type == "supplier-comparison":
        quotes = (await db.execute(select(SupplierQuote))).scalars().all()
        suppliers = {s.id: s for s in (await db.execute(select(Supplier))).scalars().all()}
        writer = csv.DictWriter(output, fieldnames=[
            "quote_id", "requirement_id", "supplier", "unit_price", "total_price",
            "quantity", "lead_time_days", "payment_terms", "availability", "warranty", "status"
        ])
        writer.writeheader()
        for q in quotes:
            sup = suppliers.get(q.supplier_id)
            writer.writerow({
                "quote_id": q.display_id, "requirement_id": q.requirement_id,
                "supplier": sup.company_name if sup else f"SUP#{q.supplier_id}",
                "unit_price": q.unit_price, "total_price": q.total_price,
                "quantity": q.quantity, "lead_time_days": q.lead_time_days,
                "payment_terms": q.payment_terms, "availability": q.availability,
                "warranty": q.warranty, "status": q.status,
            })
    else:
        from fastapi import HTTPException
        raise HTTPException(400, f"Unknown report type: {report_type}. Supported: inventory-risk, payment-due, daily-summary, supplier-comparison")

    output.seek(0)
    filename = f"scm_{report_type}_{now.strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # utf-8-sig for Excel compatibility
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
