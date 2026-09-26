"""
Unit Tests – Payment Service
Tests deterministic payment due date calculations and categorization.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.payment_service import (
    parse_payment_terms_days,
    calculate_due_date,
    categorize_payment,
    analyze_payment_due,
)


# ---------------------------------------------------------------------------
# parse_payment_terms_days
# ---------------------------------------------------------------------------

def test_parse_net_30():
    assert parse_payment_terms_days("NET 30") == 30


def test_parse_net_60():
    assert parse_payment_terms_days("NET 60") == 60


def test_parse_net_45():
    assert parse_payment_terms_days("NET 45") == 45


def test_parse_net_15():
    assert parse_payment_terms_days("NET 15") == 15


def test_parse_advance_returns_zero():
    assert parse_payment_terms_days("ADVANCE") == 0


def test_parse_cod_returns_zero():
    assert parse_payment_terms_days("COD") == 0


def test_parse_none_defaults_30():
    assert parse_payment_terms_days(None) == 30


def test_parse_empty_defaults_30():
    assert parse_payment_terms_days("") == 30


def test_parse_case_insensitive():
    assert parse_payment_terms_days("net 30") == 30


def test_parse_prefers_larger_match():
    """NET 60 should parse as 60 not 6."""
    assert parse_payment_terms_days("NET 60") == 60


# ---------------------------------------------------------------------------
# calculate_due_date
# ---------------------------------------------------------------------------

def test_due_date_net_30():
    invoice_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    due = calculate_due_date(invoice_date, "NET 30")
    assert due == datetime(2026, 1, 31, tzinfo=timezone.utc)


def test_due_date_advance():
    invoice_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    due = calculate_due_date(invoice_date, "ADVANCE")
    assert due == invoice_date  # 0 days


# ---------------------------------------------------------------------------
# categorize_payment
# ---------------------------------------------------------------------------

def test_categorize_overdue():
    assert categorize_payment(-5) == "OVERDUE"
    assert categorize_payment(-1) == "OVERDUE"


def test_categorize_due_today():
    assert categorize_payment(0) == "DUE_TODAY"


def test_categorize_due_1_3_days():
    assert categorize_payment(1) == "DUE_1_3_DAYS"
    assert categorize_payment(3) == "DUE_1_3_DAYS"


def test_categorize_due_4_7_days():
    assert categorize_payment(4) == "DUE_4_7_DAYS"
    assert categorize_payment(7) == "DUE_4_7_DAYS"


def test_categorize_due_later():
    assert categorize_payment(8) == "DUE_LATER"
    assert categorize_payment(30) == "DUE_LATER"


# ---------------------------------------------------------------------------
# analyze_payment_due (full integration)
# ---------------------------------------------------------------------------

def make_today():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def test_overdue_invoice():
    today = make_today()
    invoice_date = today - timedelta(days=40)
    result = analyze_payment_due(
        invoice_id="INV-001",
        supplier_name="Alpha Chemicals",
        amount=500_000,
        invoice_date=invoice_date,
        payment_terms="NET 30",
        today=today,
    )
    assert result.is_overdue is True
    assert result.category == "OVERDUE"
    assert result.days_until_due < 0


def test_upcoming_invoice():
    today = make_today()
    invoice_date = today - timedelta(days=27)
    result = analyze_payment_due(
        invoice_id="INV-002",
        supplier_name="Beta Industrial",
        amount=300_000,
        invoice_date=invoice_date,
        payment_terms="NET 30",
        today=today,
    )
    assert result.is_overdue is False
    assert result.category in ("DUE_1_3_DAYS", "DUE_TODAY")


def test_future_invoice():
    today = make_today()
    invoice_date = today - timedelta(days=5)
    result = analyze_payment_due(
        invoice_id="INV-003",
        supplier_name="Gamma Supplies",
        amount=200_000,
        invoice_date=invoice_date,
        payment_terms="NET 60",
        today=today,
    )
    assert result.is_overdue is False
    assert result.category == "DUE_LATER"
    assert result.days_until_due >= 50


def test_result_fields_populated():
    today = make_today()
    invoice_date = today - timedelta(days=10)
    result = analyze_payment_due(
        invoice_id="INV-TEST",
        supplier_name="Test Supplier",
        amount=100_000,
        invoice_date=invoice_date,
        payment_terms="NET 30",
        today=today,
    )
    assert result.invoice_id == "INV-TEST"
    assert result.supplier_name == "Test Supplier"
    assert result.amount == 100_000
    assert result.payment_terms_days == 30
    assert result.due_date is not None
    assert result.invoice_date is not None


def test_to_dict_has_all_fields():
    today = make_today()
    invoice_date = today - timedelta(days=10)
    result = analyze_payment_due(
        invoice_id="INV-DICT",
        supplier_name="Test",
        amount=50_000,
        invoice_date=invoice_date,
        payment_terms="NET 30",
        today=today,
    )
    d = result.to_dict()
    expected_keys = [
        "invoice_id", "supplier_name", "amount", "invoice_date",
        "payment_terms_days", "due_date", "days_until_due", "category", "is_overdue"
    ]
    for k in expected_keys:
        assert k in d
