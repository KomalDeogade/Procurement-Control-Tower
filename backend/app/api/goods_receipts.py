"""Goods Receipts API – create GRN and auto-update inventory."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.goods_receipt import GoodsReceipt
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.inventory import InventoryItem, InventoryTransaction, TransactionType
from app.models.user import User
from app.schemas import GRNCreate, GRNResponse
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/", response_model=list[GRNResponse])
async def list_goods_receipts(
    po_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(GoodsReceipt).order_by(GoodsReceipt.created_at.desc())
    if po_id:
        q = q.where(GoodsReceipt.po_id == po_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=GRNResponse, status_code=201)
async def create_goods_receipt(
    body: GRNCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate PO exists
    po = (await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == body.po_id))).scalar_one_or_none()
    if not po:
        raise HTTPException(404, "Purchase Order not found")

    all_grns = (await db.execute(select(GoodsReceipt))).scalars().all()
    display_id = f"GRN-{6001 + len(all_grns)}"

    grn = GoodsReceipt(display_id=display_id, **body.model_dump())
    db.add(grn)

    # Update PO status
    if body.received_quantity >= po.quantity * 0.99:
        po.status = POStatus.FULLY_RECEIVED
    else:
        po.status = POStatus.PARTIALLY_RECEIVED

    # Auto-update inventory
    inv_item = (await db.execute(
        select(InventoryItem).where(InventoryItem.material_code == po.material_code)
    )).scalar_one_or_none()

    if inv_item:
        inv_item.quantity_on_hand += body.received_quantity
        # Create inventory transaction
        txn = InventoryTransaction(
            inventory_item_id=inv_item.id,
            transaction_type=TransactionType.RECEIPT,
            quantity=body.received_quantity,
            reference_type="goods_receipt",
            reference_id=grn.id if grn.id else 0,
            created_by=current_user.id,
        )
        db.add(txn)
    else:
        # Create new inventory item
        new_item = InventoryItem(
            material_code=po.material_code,
            material_name=po.material_name or po.material_code,
            quantity_on_hand=body.received_quantity,
            unit="PCS",
        )
        db.add(new_item)

    await log_audit(db, current_user.username, "CREATE_GRN", "goods_receipt", display_id,
                    new_value={"po_id": po.display_id, "received_qty": body.received_quantity,
                               "quality": body.quality_status})
    await log_audit(db, "system", "INVENTORY_UPDATE", "inventory", po.material_code,
                    new_value={"added_qty": body.received_quantity})
    await db.commit()
    await db.refresh(grn)
    return grn
