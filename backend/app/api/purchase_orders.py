"""Purchase Orders API – creation, SAP sync, lifecycle management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.requirement import Requirement, RequirementStatus
from app.models.user import User
from app.schemas import POCreate, POResponse
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/", response_model=list[POResponse])
async def list_purchase_orders(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    if status:
        q = q.where(PurchaseOrder.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=POResponse, status_code=201)
async def create_purchase_order(
    body: POCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_pos = (await db.execute(select(PurchaseOrder))).scalars().all()
    po_num = 450001 + len(all_pos)
    display_id = f"PO-{po_num}"

    po = PurchaseOrder(
        display_id=display_id,
        status=POStatus.DRAFT,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(po)

    # Update requirement status
    req = (await db.execute(select(Requirement).where(Requirement.id == body.requirement_id))).scalar_one_or_none()
    if req:
        req.status = RequirementStatus.PO_CREATED

    await log_audit(db, current_user.username, "CREATE", "purchase_order", display_id,
                    new_value={"supplier_id": body.supplier_id, "total": body.total_amount})
    await db.commit()
    await db.refresh(po)
    return po


@router.get("/{po_id}", response_model=POResponse)
async def get_purchase_order(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(404, "Purchase Order not found")
    return po


@router.post("/{po_id}/sync-sap")
async def sync_with_sap(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync PO with Mock SAP – creates a SAP PO number."""
    po = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))).scalar_one_or_none()
    if not po:
        raise HTTPException(404, "Purchase Order not found")

    # Try to call Mock SAP service
    import httpx
    from app.core.config import settings

    sap_po_number = None
    sap_status = "FAILED"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{settings.MOCK_SAP_URL}/sap/purchase-orders", json={
                "supplier_id": f"SUP-{po.supplier_id:03d}",
                "material_code": po.material_code,
                "quantity": po.quantity,
                "unit_price": po.unit_price,
                "requirement_id": po.display_id,
            })
            if resp.status_code == 200:
                data = resp.json()
                sap_po_number = data.get("purchase_order_number")
                sap_status = "SYNCHRONIZED"
    except Exception:
        # Mock SAP might not be running; generate a mock PO number locally
        import random
        sap_po_number = str(450001000 + random.randint(1, 9999))
        sap_status = "SYNCHRONIZED (local mock)"

    po.sap_po_number = sap_po_number
    po.status = POStatus.SAP_CREATED

    await log_audit(db, current_user.username, "SAP_SYNC", "purchase_order",
                    po.display_id or str(po.id),
                    new_value={"sap_po_number": sap_po_number, "status": sap_status})
    await db.commit()
    await db.refresh(po)

    return {
        "po_id": po.display_id,
        "sap_po_number": sap_po_number,
        "sync_status": sap_status,
        "disclaimer": "⚠ Mock SAP – not a real SAP transaction",
    }
