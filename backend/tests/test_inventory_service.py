"""
Unit Tests – Inventory Service
Tests deterministic inventory calculations with no DB dependencies.
"""

import pytest
from datetime import date, timedelta
from app.services.inventory_service import calculate_inventory_analysis


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_analysis(**overrides):
    defaults = {
        "material_code": "MAT-001",
        "material_name": "Industrial Lubricant XLR-500",
        "quantity_on_hand": 2000.0,
        "reserved_quantity": 200.0,
        "safety_stock": 500.0,
        "minimum_stock": 300.0,
        "reorder_level": 800.0,
        "average_daily_consumption": 50.0,
        "lead_time_days": 14,
        "open_po_quantity": 0.0,
    }
    defaults.update(overrides)
    return calculate_inventory_analysis(**defaults)


# ---------------------------------------------------------------------------
# Available Stock
# ---------------------------------------------------------------------------

def test_available_stock_calculation():
    a = make_analysis(quantity_on_hand=2000, reserved_quantity=200)
    assert a.available_stock == 1800.0


def test_available_stock_zero_reserved():
    a = make_analysis(quantity_on_hand=1000, reserved_quantity=0)
    assert a.available_stock == 1000.0


def test_available_stock_can_be_negative():
    """When reserved > on_hand we allow negative available (over-reserved)."""
    a = make_analysis(quantity_on_hand=100, reserved_quantity=300)
    assert a.available_stock == -200.0


# ---------------------------------------------------------------------------
# Risk Status
# ---------------------------------------------------------------------------

def test_risk_status_normal():
    # available_stock=1800, reorder_level=800, safety_stock=500 → NORMAL
    a = make_analysis()
    assert a.risk_status == "NORMAL"


def test_risk_status_low_when_below_reorder():
    # available = 700, reorder_level = 800 → LOW
    a = make_analysis(quantity_on_hand=900, reserved_quantity=200, reorder_level=800, safety_stock=500)
    assert a.risk_status == "LOW"


def test_risk_status_critical_when_at_safety_stock():
    # available = 400, safety_stock = 500 → CRITICAL
    a = make_analysis(quantity_on_hand=600, reserved_quantity=200, safety_stock=500, reorder_level=800)
    assert a.risk_status == "CRITICAL"


def test_risk_status_stockout_when_zero_or_negative():
    a = make_analysis(quantity_on_hand=200, reserved_quantity=200)
    assert a.risk_status == "STOCKOUT_RISK"


def test_risk_status_critical_when_coverage_less_than_lead_time():
    # available=500, daily_consumption=100 → coverage=5 days, lead_time=14 → CRITICAL
    a = make_analysis(
        quantity_on_hand=700, reserved_quantity=200,
        average_daily_consumption=100,
        lead_time_days=14,
        safety_stock=100,
        reorder_level=300,
    )
    assert a.risk_status == "CRITICAL"


# ---------------------------------------------------------------------------
# Stock Coverage Days
# ---------------------------------------------------------------------------

def test_stock_coverage_days_calculated():
    # available=1800, daily_consumption=50 → 36 days
    a = make_analysis()
    assert a.stock_coverage_days == 36.0


def test_stock_coverage_days_zero_consumption():
    a = make_analysis(average_daily_consumption=0.0)
    assert a.stock_coverage_days is None
    assert a.projected_stockout_date is None


def test_projected_stockout_date_is_future():
    a = make_analysis()
    assert a.projected_stockout_date is not None
    stockout_date = date.fromisoformat(a.projected_stockout_date)
    assert stockout_date > date.today()


# ---------------------------------------------------------------------------
# Replenishment Recommendation
# ---------------------------------------------------------------------------

def test_no_reorder_needed_when_stock_high():
    # available=1800, safety=500, lead_time=14, consumption=50 → 700 needed during lead, target=1200
    # 1800 > 1200 → no reorder
    a = make_analysis()
    assert a.recommended_reorder_qty == 0.0
    assert "No replenishment" in a.reorder_reason


def test_reorder_qty_when_stock_low():
    # available=200, safety=500, daily=50, lead=14 → need 500+(50*14)=1200, minus 200 avail → 1000
    a = make_analysis(quantity_on_hand=400, reserved_quantity=200)
    assert a.recommended_reorder_qty > 0


def test_open_po_reduces_reorder_qty():
    a_without_po = make_analysis(quantity_on_hand=400, reserved_quantity=200, open_po_quantity=0)
    a_with_po = make_analysis(quantity_on_hand=400, reserved_quantity=200, open_po_quantity=500)
    assert a_with_po.recommended_reorder_qty <= a_without_po.recommended_reorder_qty


def test_reorder_qty_never_negative():
    a = make_analysis(open_po_quantity=100000)
    assert a.recommended_reorder_qty >= 0


# ---------------------------------------------------------------------------
# Output fields
# ---------------------------------------------------------------------------

def test_to_dict_has_all_fields():
    a = make_analysis()
    d = a.to_dict()
    expected = [
        "material_code", "material_name", "quantity_on_hand", "reserved_quantity",
        "available_stock", "safety_stock", "minimum_stock", "reorder_level",
        "average_daily_consumption", "lead_time_days", "stock_coverage_days",
        "projected_stockout_date", "risk_status", "risk_message",
        "open_po_quantity", "recommended_reorder_qty", "reorder_reason"
    ]
    for key in expected:
        assert key in d


def test_risk_message_mentions_material_name():
    a = make_analysis(quantity_on_hand=100, reserved_quantity=200)
    assert "Industrial Lubricant XLR-500" in a.risk_message
