"""
Inventory calculation service – deterministic formulas.

Available Stock = Current Stock - Reserved Quantity
Stock Coverage Days = Available Stock / Average Daily Consumption
Projected Stockout Date = Today + Stock Coverage Days
"""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from app.models.inventory import StockRiskStatus


@dataclass
class InventoryAnalysis:
    material_code: str
    material_name: str
    quantity_on_hand: float
    reserved_quantity: float
    available_stock: float
    safety_stock: float
    minimum_stock: float
    reorder_level: float
    average_daily_consumption: float
    lead_time_days: int
    stock_coverage_days: float | None
    projected_stockout_date: str | None
    risk_status: str
    risk_message: str
    open_po_quantity: float
    recommended_reorder_qty: float
    reorder_reason: str

    def to_dict(self) -> dict:
        return {
            "material_code": self.material_code,
            "material_name": self.material_name,
            "quantity_on_hand": self.quantity_on_hand,
            "reserved_quantity": self.reserved_quantity,
            "available_stock": self.available_stock,
            "safety_stock": self.safety_stock,
            "minimum_stock": self.minimum_stock,
            "reorder_level": self.reorder_level,
            "average_daily_consumption": self.average_daily_consumption,
            "lead_time_days": self.lead_time_days,
            "stock_coverage_days": self.stock_coverage_days,
            "projected_stockout_date": self.projected_stockout_date,
            "risk_status": self.risk_status,
            "risk_message": self.risk_message,
            "open_po_quantity": self.open_po_quantity,
            "recommended_reorder_qty": self.recommended_reorder_qty,
            "reorder_reason": self.reorder_reason,
        }


def calculate_inventory_analysis(
    material_code: str,
    material_name: str,
    quantity_on_hand: float,
    reserved_quantity: float,
    safety_stock: float,
    minimum_stock: float,
    reorder_level: float,
    average_daily_consumption: float,
    lead_time_days: int,
    open_po_quantity: float = 0.0,
) -> InventoryAnalysis:
    """Compute all inventory metrics deterministically."""

    available_stock = quantity_on_hand - reserved_quantity

    # Stock coverage days
    stock_coverage_days: float | None = None
    projected_stockout_date: str | None = None

    if average_daily_consumption > 0:
        stock_coverage_days = round(available_stock / average_daily_consumption, 1)
        projected_date = datetime.now(timezone.utc) + timedelta(days=max(0, stock_coverage_days))
        projected_stockout_date = projected_date.strftime("%Y-%m-%d")

    # Risk assessment
    risk_status = StockRiskStatus.NORMAL.value
    risk_message = "Stock levels are adequate."

    if available_stock <= 0:
        risk_status = StockRiskStatus.STOCKOUT_RISK.value
        risk_message = f"STOCKOUT: {material_name} has zero or negative available stock."
    elif available_stock <= safety_stock:
        risk_status = StockRiskStatus.CRITICAL.value
        risk_message = f"CRITICAL: {material_name} is below safety stock ({available_stock:.0f} vs {safety_stock:.0f})."
    elif available_stock <= reorder_level:
        risk_status = StockRiskStatus.LOW.value
        risk_message = f"LOW: {material_name} is below reorder level ({available_stock:.0f} vs {reorder_level:.0f})."
    elif stock_coverage_days is not None and stock_coverage_days <= lead_time_days:
        risk_status = StockRiskStatus.CRITICAL.value
        risk_message = (
            f"CRITICAL: {material_name} may fall below safety stock in {stock_coverage_days} days "
            f"(lead time: {lead_time_days} days)."
        )

    # Replenishment recommendation
    consumption_during_lead = average_daily_consumption * lead_time_days
    target_stock = safety_stock + consumption_during_lead
    needed = max(0, target_stock - available_stock - open_po_quantity)
    recommended_reorder_qty = round(needed, 0)

    if recommended_reorder_qty > 0:
        reorder_reason = (
            f"Need {recommended_reorder_qty:.0f} units to cover {lead_time_days}-day lead time "
            f"({consumption_during_lead:.0f} consumption) + safety stock ({safety_stock:.0f}), "
            f"minus {open_po_quantity:.0f} on open POs."
        )
    else:
        reorder_reason = "No replenishment needed at this time."

    return InventoryAnalysis(
        material_code=material_code,
        material_name=material_name,
        quantity_on_hand=quantity_on_hand,
        reserved_quantity=reserved_quantity,
        available_stock=available_stock,
        safety_stock=safety_stock,
        minimum_stock=minimum_stock,
        reorder_level=reorder_level,
        average_daily_consumption=average_daily_consumption,
        lead_time_days=lead_time_days,
        stock_coverage_days=stock_coverage_days,
        projected_stockout_date=projected_stockout_date,
        risk_status=risk_status,
        risk_message=risk_message,
        open_po_quantity=open_po_quantity,
        recommended_reorder_qty=recommended_reorder_qty,
        reorder_reason=reorder_reason,
    )
