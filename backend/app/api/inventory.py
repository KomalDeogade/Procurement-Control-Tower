"""Inventory API – stock levels, risk analysis, replenishment recommendations."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.inventory import InventoryItem
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.user import User
from app.schemas import InventoryResponse
from app.services.inventory_service import calculate_inventory_analysis

router = APIRouter()


@router.get("/", response_model=list[InventoryResponse])
async def list_inventory(
    risk_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).order_by(InventoryItem.material_code))
    items = result.scalars().all()
    if risk_only:
        risky = []
        for item in items:
            avail = item.quantity_on_hand - item.reserved_quantity
            if avail <= item.reorder_level:
                risky.append(item)
        return risky
    return items


@router.get("/analysis")
async def inventory_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run full inventory analysis across all materials."""
    items = (await db.execute(select(InventoryItem).order_by(InventoryItem.material_code))).scalars().all()

    analyses = []
    for item in items:
        # Get open PO quantity
        open_pos = (await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.material_code == item.material_code,
                PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.SAP_CREATED, POStatus.PARTIALLY_RECEIVED]),
            )
        )).scalars().all()
        open_po_qty = sum(po.quantity for po in open_pos)

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
            open_po_quantity=open_po_qty,
        )
        analyses.append(analysis.to_dict())

    # Sort by risk (critical first)
    risk_order = {"STOCKOUT_RISK": 0, "CRITICAL": 1, "LOW": 2, "NORMAL": 3}
    analyses.sort(key=lambda a: risk_order.get(a["risk_status"], 4))

    risk_summary = {
        "total_materials": len(analyses),
        "normal": sum(1 for a in analyses if a["risk_status"] == "NORMAL"),
        "low": sum(1 for a in analyses if a["risk_status"] == "LOW"),
        "critical": sum(1 for a in analyses if a["risk_status"] == "CRITICAL"),
        "stockout_risk": sum(1 for a in analyses if a["risk_status"] == "STOCKOUT_RISK"),
    }

    return {"summary": risk_summary, "items": analyses}


@router.get("/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "Inventory item not found")
    return item


@router.get("/{item_id}/analysis")
async def item_analysis(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Single item analysis with replenishment recommendation."""
    item = (await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))).scalar_one_or_none()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "Inventory item not found")

    open_pos = (await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.material_code == item.material_code,
            PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.SAP_CREATED]),
        )
    )).scalars().all()

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
        open_po_quantity=sum(po.quantity for po in open_pos),
    )
    return analysis.to_dict()
