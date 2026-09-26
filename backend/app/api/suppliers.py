"""Suppliers API – full CRUD with search/filter."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter()


@router.get("/", response_model=list[SupplierResponse])
async def list_suppliers(
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Supplier).order_by(Supplier.company_name)
    if search:
        q = q.where(or_(
            Supplier.company_name.ilike(f"%{search}%"),
            Supplier.supplier_code.ilike(f"%{search}%"),
            Supplier.category.ilike(f"%{search}%"),
            Supplier.location.ilike(f"%{search}%"),
        ))
    if category:
        q = q.where(Supplier.category == category)
    if status:
        q = q.where(Supplier.approval_status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    body: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-generate supplier_code if not provided
    if not body.supplier_code:
        count = (await db.execute(select(Supplier))).scalars().all()
        body.supplier_code = f"SUP-{len(count) + 1:03d}"
    supplier = Supplier(**body.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    await db.commit()
    await db.refresh(supplier)
    return supplier
