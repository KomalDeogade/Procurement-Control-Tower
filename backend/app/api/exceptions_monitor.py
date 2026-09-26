"""
Exceptions & Monitoring API – Exception-first automation.

Endpoints:
  GET /exceptions/          – All current exceptions
  GET /exceptions/activity  – Activity feed (recent events)
  GET /exceptions/watchdog  – Payment watchdog report
  POST /exceptions/advance-payment-check – Advance payment supplier workflow
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
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
from app.models.audit_log import AuditLog
from app.services.payment_service import categorize_payment

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# Exception categories
# ─────────────────────────────────────────────────────────────

EXCEPTION_NORMAL = "NORMAL"
EXCEPTION_WARN   = "WARNING"
EXCEPTION_HIGH   = "HIGH"
EXCEPTION_CRIT   = "CRITICAL"


def _exc(category: str, exc_type: str, title: str, detail: str,
         entity_type: str, entity_id, action: str | None = None) -> dict:
    return {
        "category": category,
        "type": exc_type,
        "title": title,
        "detail": detail,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "recommended_action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/")
async def get_exceptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Collect all current exceptions across the procurement workflow.
    Normal-case items are filtered out — only exceptions surface here.
    """
    now = datetime.utcnow()
    exceptions: list[dict] = []

    # ── 1. Invoice 3-way match discrepancies ──────────────────
    discrepancies = (await db.execute(
        select(Invoice).where(Invoice.status == "DISCREPANCY")
    )).scalars().all()
    for inv in discrepancies:
        exceptions.append(_exc(
            EXCEPTION_HIGH, "INVOICE_MISMATCH",
            f"3-Way Match Failed: {inv.display_id}",
            f"Invoice {inv.display_id} (₹{inv.total_amount:,.0f}) has quantity/price discrepancy",
            "invoice", inv.id,
            "Review invoice, contact supplier, run 3-way match again"
        ))

    # ── 2. Overdue invoices ────────────────────────────────────
    overdue = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date <= now
        )
    )).scalars().all()
    for inv in overdue:
        due = inv.due_date.replace(tzinfo=None) if inv.due_date else now
        days_over = abs((due - now).days)
        exceptions.append(_exc(
            EXCEPTION_CRIT, "OVERDUE_PAYMENT",
            f"Overdue Payment: {inv.display_id}",
            f"Invoice {inv.display_id} is {days_over} day(s) overdue. Amount: ₹{inv.total_amount:,.0f}",
            "invoice", inv.id,
            "Initiate payment immediately or escalate to finance"
        ))

    # ── 3. Invoices due in 3 days ──────────────────────────────
    due_soon = (await db.execute(
        select(Invoice).where(
            Invoice.status.in_(["VALIDATED", "APPROVED"]),
            Invoice.due_date > now,
            Invoice.due_date <= now + timedelta(days=3),
        )
    )).scalars().all()
    for inv in due_soon:
        due = inv.due_date.replace(tzinfo=None) if inv.due_date else now
        days_left = (due - now).days
        exceptions.append(_exc(
            EXCEPTION_HIGH, "PAYMENT_DUE_SOON",
            f"Payment Due in {days_left} Day(s): {inv.display_id}",
            f"Invoice {inv.display_id} (₹{inv.total_amount:,.0f}) due in {days_left} day(s)",
            "invoice", inv.id,
            "Process payment or request extension"
        ))

    # ── 4. Critical / stockout inventory ──────────────────────
    items = (await db.execute(select(InventoryItem))).scalars().all()
    for item in items:
        avail = item.quantity_on_hand - item.reserved_quantity
        if avail <= 0:
            exceptions.append(_exc(
                EXCEPTION_CRIT, "STOCKOUT_RISK",
                f"Stockout Risk: {item.material_name}",
                f"{item.material_code} has zero/negative available stock ({avail:.0f} units). Safety stock: {item.safety_stock:.0f}",
                "inventory", item.id,
                "Create emergency replenishment request immediately"
            ))
        elif avail <= item.safety_stock:
            daily = item.average_daily_consumption or 1
            days_cover = avail / daily if daily > 0 else 0
            exceptions.append(_exc(
                EXCEPTION_HIGH, "STOCK_CRITICAL",
                f"Critical Stock Level: {item.material_name}",
                f"{item.material_code} has {avail:.0f} units available ({days_cover:.0f} days coverage). Lead time: {item.lead_time_days}d",
                "inventory", item.id,
                f"Initiate replenishment order. Reorder quantity: {max(0, item.reorder_level - avail):.0f} units"
            ))

    # ── 5. High-risk suppliers with active quotes/POs ─────────
    high_risk = (await db.execute(
        select(Supplier).where(Supplier.risk_score >= 60)
    )).scalars().all()
    for sup in high_risk:
        # Check if they have active POs
        active_po = (await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.supplier_id == sup.id,
                PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED", "PARTIALLY_RECEIVED"])
            ).limit(1)
        )).scalar_one_or_none()
        if active_po:
            exceptions.append(_exc(
                EXCEPTION_HIGH, "HIGH_RISK_SUPPLIER_ACTIVE",
                f"High-Risk Supplier with Active PO: {sup.company_name}",
                f"{sup.company_name} has risk score {sup.risk_score}/100 with active PO {active_po.display_id}",
                "supplier", sup.id,
                "Review supplier risk assessment and consider mitigation"
            ))

    # ── 6. Quotes needing review (AI extraction incomplete) ───
    needs_review = (await db.execute(
        select(SupplierQuote).where(SupplierQuote.status == "NEEDS_REVIEW")
    )).scalars().all()
    for quote in needs_review:
        exceptions.append(_exc(
            EXCEPTION_WARN, "QUOTE_NEEDS_REVIEW",
            f"Quote Requires Review: {quote.display_id}",
            f"AI-extracted quote {quote.display_id} has missing/unclear fields",
            "quote", quote.id,
            "Review and complete missing fields before scoring"
        ))

    # ── 7. POs over budget ────────────────────────────────────
    pos = (await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED"]))
    )).scalars().all()
    for po in pos:
        req = (await db.execute(
            select(Requirement).where(Requirement.id == po.requirement_id)
        )).scalar_one_or_none()
        if req and req.budget and po.total_amount > req.budget * 1.05:
            overage_pct = round(((po.total_amount - req.budget) / req.budget) * 100, 1)
            exceptions.append(_exc(
                EXCEPTION_HIGH, "PO_OVER_BUDGET",
                f"PO Exceeds Budget: {po.display_id}",
                f"PO {po.display_id} (₹{po.total_amount:,.0f}) is {overage_pct}% over approved budget (₹{req.budget:,.0f})",
                "purchase_order", po.id,
                "Escalate for budget approval or negotiate with supplier"
            ))

    # Sort: CRITICAL → HIGH → WARNING
    priority = {EXCEPTION_CRIT: 0, EXCEPTION_HIGH: 1, EXCEPTION_WARN: 2, EXCEPTION_NORMAL: 3}
    exceptions.sort(key=lambda x: priority.get(x["category"], 9))

    return {
        "count": len(exceptions),
        "critical": len([e for e in exceptions if e["category"] == EXCEPTION_CRIT]),
        "high": len([e for e in exceptions if e["category"] == EXCEPTION_HIGH]),
        "warning": len([e for e in exceptions if e["category"] == EXCEPTION_WARN]),
        "exceptions": exceptions,
        "generated_at": now.isoformat(),
    }


@router.get("/activity")
async def get_activity_feed(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activity feed — recent audit events formatted for timeline display.
    Makes the system feel operational.
    """
    logs = (await db.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    )).scalars().all()

    # Map action → human-readable message
    ACTION_MESSAGES = {
        "CREATE": lambda e, id: f"Created {e.replace('_', ' ').lower()} {id}",
        "SUBMIT": lambda e, id: f"Submitted {e.replace('_', ' ').lower()} {id} for processing",
        "UPDATE": lambda e, id: f"Updated {e.replace('_', ' ').lower()} {id}",
        "APPROVED": lambda e, id: f"✅ Approved {e.replace('_', ' ').lower()} {id}",
        "REJECTED": lambda e, id: f"❌ Rejected {e.replace('_', ' ').lower()} {id}",
        "REVISION_REQUIRED": lambda e, id: f"🔄 Revision requested for {e.replace('_', ' ').lower()} {id}",
        "SAP_SYNC": lambda e, id: f"🔗 Mock SAP synchronization completed for {id}",
        "THREE_WAY_MATCH": lambda e, id: f"⚖️ 3-way match executed for invoice {id}",
        "PROCESS_PAYMENT": lambda e, id: f"💳 Mock payment processed for {id}",
        "GENERATE_RFQS": lambda e, id: f"📨 RFQs generated for requirement {id}",
        "SUBMIT_QUOTE": lambda e, id: f"📥 Supplier quote received: {id}",
        "COMPARE_QUOTES": lambda e, id: f"📊 Quote comparison completed for requirement {id}",
        "CREATE_GRN": lambda e, id: f"📫 Goods receipt recorded: {id}",
        "INVENTORY_UPDATE": lambda e, id: f"📦 Inventory updated for {id}",
        "CREATE_APPROVAL": lambda e, id: f"🔔 Approval requested for {e.replace('_', ' ').lower()} {id}",
        "AI_EXTRACT_QUOTE": lambda e, id: f"🤖 AI extracted quotation data from document",
        "AI_DRAFT_EMAIL": lambda e, id: f"🤖 AI drafted negotiation email",
    }

    def format_activity(log: AuditLog) -> dict:
        actor_label = log.actor if log.actor != "system" else "System"
        fn = ACTION_MESSAGES.get(log.action, lambda e, id: f"{log.action.replace('_', ' ').title()}: {id}")
        message = fn(log.entity_type, log.entity_id)

        icon_map = {
            "AI_": "🤖",
            "APPROVED": "✅",
            "REJECTED": "❌",
            "SAP": "🔗",
            "PAYMENT": "💳",
            "THREE_WAY": "⚖️",
            "GRN": "📫",
            "INVENTORY": "📦",
            "QUOTE": "📊",
            "RFQ": "📨",
            "CREATE": "➕",
            "UPDATE": "✏️",
            "SUBMIT": "📤",
        }
        icon = "📋"
        for prefix, i in icon_map.items():
            if log.action.startswith(prefix) or prefix in log.action:
                icon = i
                break

        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "actor": actor_label,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "message": message,
            "icon": icon,
        }

    return {
        "count": len(logs),
        "activities": [format_activity(l) for l in logs],
    }


@router.get("/watchdog")
async def payment_watchdog(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Payment watchdog — daily monitoring of all payment due dates.
    Categorizes by urgency for dashboard alerts.
    """
    from app.services.payment_service import analyze_payment_due, parse_payment_terms_days
    now = datetime.now(timezone.utc)

    invoices = (await db.execute(
        select(Invoice).where(Invoice.status.in_(["SUBMITTED", "VALIDATED", "APPROVED", "PAYMENT_PENDING"]))
    )).scalars().all()

    categories: dict[str, list] = {
        "OVERDUE": [],
        "DUE_TODAY": [],
        "DUE_1_3_DAYS": [],
        "DUE_4_7_DAYS": [],
        "DUE_LATER": [],
    }

    total_exposure = 0.0
    overdue_amount = 0.0

    for inv in invoices:
        due = inv.due_date or (inv.invoice_date + timedelta(days=30) if inv.invoice_date else now)
        days_until = (due.date() - now.date()).days if hasattr(due, 'date') else (due - now).days
        cat = categorize_payment(days_until)

        supplier = (await db.execute(select(Supplier).where(Supplier.id == inv.supplier_id))).scalar_one_or_none()

        item = {
            "invoice_id": inv.display_id,
            "supplier_name": supplier.company_name if supplier else f"SUP#{inv.supplier_id}",
            "amount": inv.total_amount,
            "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else None,
            "due_date": due.strftime("%Y-%m-%d") if hasattr(due, 'strftime') else str(due),
            "days_until_due": days_until,
            "category": cat,
        }

        categories[cat].append(item)
        total_exposure += inv.total_amount
        if cat == "OVERDUE":
            overdue_amount += inv.total_amount

    return {
        "generated_at": now.isoformat(),
        "total_monitored": len(invoices),
        "total_exposure": total_exposure,
        "overdue_count": len(categories["OVERDUE"]),
        "overdue_amount": overdue_amount,
        "due_today_count": len(categories["DUE_TODAY"]),
        "categories": categories,
    }


@router.post("/advance-payment-check")
async def advance_payment_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check advance-payment suppliers for replenishment threshold.
    Suppliers with ADVANCE payment terms and active POs are monitored.
    Creates alerts when balance may be insufficient.
    Does NOT automatically transfer money.
    """
    now = datetime.now(timezone.utc)

    # Find suppliers with advance payment terms
    advance_suppliers = (await db.execute(
        select(Supplier).where(Supplier.payment_terms.ilike("%ADVANCE%"))
    )).scalars().all()

    alerts = []
    for sup in advance_suppliers:
        # Check active POs
        active_pos = (await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.supplier_id == sup.id,
                PurchaseOrder.status.in_(["DRAFT", "SAP_CREATED", "PARTIALLY_RECEIVED"])
            )
        )).scalars().all()

        if not active_pos:
            continue

        total_committed = sum(po.total_amount for po in active_pos)

        # Check payments made to this supplier
        paid_invoices = (await db.execute(
            select(Invoice).where(
                Invoice.supplier_id == sup.id,
                Invoice.status == "PAID"
            )
        )).scalars().all()
        total_paid = sum(inv.total_amount for inv in paid_invoices)

        # Pending invoices (advance payment obligations)
        pending_invoices = (await db.execute(
            select(Invoice).where(
                Invoice.supplier_id == sup.id,
                Invoice.status.in_(["SUBMITTED", "VALIDATED", "APPROVED", "PAYMENT_PENDING"])
            )
        )).scalars().all()
        pending_amount = sum(inv.total_amount for inv in pending_invoices)

        alerts.append({
            "supplier_id": sup.id,
            "supplier_name": sup.company_name,
            "payment_terms": sup.payment_terms,
            "active_pos": len(active_pos),
            "committed_amount": total_committed,
            "total_paid": total_paid,
            "pending_obligations": pending_amount,
            "risk_level": "HIGH" if pending_amount > 0 else "NORMAL",
            "alert_message": (
                f"⚠️ Advance payment supplier {sup.company_name} has ₹{pending_amount:,.0f} in pending obligations. "
                f"Approval required before goods delivery."
            ) if pending_amount > 0 else None,
            "requires_approval": pending_amount > 0,
        })

    return {
        "advance_payment_suppliers": len(alerts),
        "alerts": alerts,
        "disclaimer": "No automatic payments are initiated. All advance payments require explicit human approval.",
        "generated_at": now.isoformat(),
    }
