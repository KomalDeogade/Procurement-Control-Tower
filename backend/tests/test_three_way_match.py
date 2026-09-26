"""
Unit Tests – Three-Way Match Service
Tests deterministic PO/GRN/Invoice matching logic.
"""

import pytest
from app.services.three_way_match import three_way_match, _variance_pct, MatchResult


# ---------------------------------------------------------------------------
# Variance percentage helper
# ---------------------------------------------------------------------------

def test_variance_pct_zero_expected_nonzero_actual():
    assert _variance_pct(0, 100) == 100.0


def test_variance_pct_zero_both():
    assert _variance_pct(0, 0) == 0.0


def test_variance_pct_exact_match():
    assert _variance_pct(100, 100) == 0.0


def test_variance_pct_over():
    assert _variance_pct(100, 110) == 10.0


def test_variance_pct_under():
    assert _variance_pct(100, 90) == -10.0


# ---------------------------------------------------------------------------
# Perfect match (all within tolerance)
# ---------------------------------------------------------------------------

def test_perfect_match_returns_matched():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
    )
    assert result.status == "MATCHED"
    assert result.quantity_match is True
    assert result.price_match is True
    assert result.amount_match is True
    assert len(result.exceptions) == 0


# ---------------------------------------------------------------------------
# Quantity mismatch
# ---------------------------------------------------------------------------

def test_quantity_mismatch_grn_under():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=4000,  # 20% short
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
    )
    assert result.status == "MISMATCH"
    assert result.quantity_match is False
    assert any("GRN" in e for e in result.exceptions)


def test_quantity_mismatch_invoice_over():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5500,  # 10% over
        invoice_unit_price=1600, invoice_total=8_800_000,
    )
    assert result.status == "MISMATCH"
    assert result.quantity_match is False


# ---------------------------------------------------------------------------
# Price mismatch
# ---------------------------------------------------------------------------

def test_price_mismatch_invoice_higher():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5000, invoice_unit_price=1800, invoice_total=9_000_000,
    )
    assert result.status == "MISMATCH"
    assert result.price_match is False
    assert any("unit price" in e.lower() for e in result.exceptions)


def test_price_mismatch_invoice_lower():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5000, invoice_unit_price=1400, invoice_total=7_000_000,
    )
    # Price 12.5% lower than PO — outside 5% tolerance
    assert result.status == "MISMATCH"
    assert result.price_match is False


# ---------------------------------------------------------------------------
# Tolerance boundary conditions
# ---------------------------------------------------------------------------

def test_within_tolerance_still_matched():
    """Exactly 5% variance should still pass."""
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5250,  # Exactly 5% over
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
    )
    assert result.quantity_match is True


def test_just_outside_tolerance_fails():
    """5.01% variance should fail."""
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5251,  # Slightly over 5%
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
    )
    assert result.quantity_match is False


def test_custom_tolerance():
    """A 10% tolerance should allow 8% variance."""
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5400,  # 8% over
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
        tolerance_pct=10.0,
    )
    assert result.quantity_match is True


# ---------------------------------------------------------------------------
# Amount mismatch
# ---------------------------------------------------------------------------

def test_amount_mismatch():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5000, invoice_unit_price=1600,
        invoice_total=9_000_000,  # 12.5% over
    )
    assert result.amount_match is False
    assert any("total" in e.lower() for e in result.exceptions)


# ---------------------------------------------------------------------------
# Multiple exceptions
# ---------------------------------------------------------------------------

def test_multiple_exceptions_reported():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=4000,  # qty mismatch
        invoice_quantity=6000,  # qty mismatch
        invoice_unit_price=2000,  # price mismatch
        invoice_total=12_000_000,  # amount mismatch
    )
    assert result.status == "MISMATCH"
    assert len(result.exceptions) >= 3


# ---------------------------------------------------------------------------
# MatchResult.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_has_all_fields():
    result = three_way_match(
        po_quantity=5000, po_unit_price=1600, po_total=8_000_000,
        grn_quantity=5000,
        invoice_quantity=5000, invoice_unit_price=1600, invoice_total=8_000_000,
    )
    d = result.to_dict()
    expected_keys = [
        "status", "quantity_match", "price_match", "amount_match",
        "po_quantity", "grn_quantity", "invoice_quantity",
        "po_unit_price", "invoice_unit_price", "po_total", "invoice_total",
        "quantity_variance_pct", "price_variance_pct", "amount_variance_pct", "exceptions"
    ]
    for k in expected_keys:
        assert k in d
