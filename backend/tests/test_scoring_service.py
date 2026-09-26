"""
Unit Tests – Scoring Service
Tests the deterministic scoring logic with no DB or external dependencies.
"""

import pytest
from app.services.scoring_service import (
    score_suppliers,
    generate_explanation,
    _normalize_price_score,
    _normalize_delivery_score,
    _normalize_availability_score,
    _normalize_payment_terms_score,
    ScoreBreakdown,
)


# ---------------------------------------------------------------------------
# Price normalization tests
# ---------------------------------------------------------------------------

def test_price_score_lowest_gets_100():
    prices = [100.0, 200.0, 300.0]
    assert _normalize_price_score(prices, 100.0) == 100.0


def test_price_score_highest_gets_0():
    prices = [100.0, 200.0, 300.0]
    assert _normalize_price_score(prices, 300.0) == 0.0


def test_price_score_mid_range():
    prices = [100.0, 200.0, 300.0]
    score = _normalize_price_score(prices, 200.0)
    assert 49.0 <= score <= 51.0  # Should be ~50


def test_price_score_all_same():
    prices = [150.0, 150.0, 150.0]
    assert _normalize_price_score(prices, 150.0) == 100.0


def test_price_score_empty_list():
    assert _normalize_price_score([], 100.0) == 0.0


def test_price_score_zero_price():
    assert _normalize_price_score([100.0, 200.0], 0.0) == 0.0


# ---------------------------------------------------------------------------
# Delivery normalization tests
# ---------------------------------------------------------------------------

def test_delivery_score_shortest_gets_100():
    lead_times = [7, 14, 30]
    assert _normalize_delivery_score(lead_times, 7) == 100.0


def test_delivery_score_longest_gets_0():
    lead_times = [7, 14, 30]
    assert _normalize_delivery_score(lead_times, 30) == 0.0


def test_delivery_score_all_same():
    lead_times = [14, 14, 14]
    assert _normalize_delivery_score(lead_times, 14) == 100.0


# ---------------------------------------------------------------------------
# Availability normalization tests
# ---------------------------------------------------------------------------

def test_availability_immediate():
    assert _normalize_availability_score("In Stock") == 100.0
    assert _normalize_availability_score("immediate delivery") == 100.0


def test_availability_1_week():
    assert _normalize_availability_score("1 week") == 85.0


def test_availability_1_month():
    assert _normalize_availability_score("1 month") == 40.0


def test_availability_none():
    assert _normalize_availability_score(None) == 50.0


def test_availability_unknown():
    assert _normalize_availability_score("custom") == 50.0


# ---------------------------------------------------------------------------
# Payment terms tests
# ---------------------------------------------------------------------------

def test_payment_terms_net60_is_best():
    assert _normalize_payment_terms_score("NET 60") == 100.0


def test_payment_terms_advance_is_worst():
    assert _normalize_payment_terms_score("ADVANCE") == 20.0


def test_payment_terms_none():
    assert _normalize_payment_terms_score(None) == 50.0


def test_payment_terms_case_insensitive():
    assert _normalize_payment_terms_score("net 30") == 70.0


# ---------------------------------------------------------------------------
# Full scoring pipeline tests
# ---------------------------------------------------------------------------

SAMPLE_QUOTES = [
    {
        "supplier_id": 1,
        "supplier_name": "Alpha Chemicals",
        "total_price": 80_00_000.0,
        "unit_price": 1600.0,
        "quantity": 5000,
        "lead_time_days": 7,
        "availability": "In Stock",
        "payment_terms": "NET 60",
        "warranty": "12 months",
        "quality_score": 90.0,
        "delivery_score": 88.0,
        "risk_score": 20.0,
        "historical_performance": 85.0,
    },
    {
        "supplier_id": 2,
        "supplier_name": "Beta Industrial",
        "total_price": 75_00_000.0,
        "unit_price": 1500.0,
        "quantity": 5000,
        "lead_time_days": 21,
        "availability": "Within 3 weeks",
        "payment_terms": "NET 30",
        "warranty": "6 months",
        "quality_score": 70.0,
        "delivery_score": 72.0,
        "risk_score": 45.0,
        "historical_performance": 70.0,
    },
    {
        "supplier_id": 3,
        "supplier_name": "Gamma Supplies",
        "total_price": 95_00_000.0,
        "unit_price": 1900.0,
        "quantity": 5000,
        "lead_time_days": 14,
        "availability": "Within 2 weeks",
        "payment_terms": "ADVANCE",
        "warranty": "24 months",
        "quality_score": 55.0,
        "delivery_score": 60.0,
        "risk_score": 70.0,
        "historical_performance": 58.0,
    },
]


def test_score_suppliers_returns_three_results():
    results = score_suppliers(SAMPLE_QUOTES)
    assert len(results) == 3


def test_score_suppliers_sorted_descending():
    results = score_suppliers(SAMPLE_QUOTES)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_only_first_is_recommended():
    results = score_suppliers(SAMPLE_QUOTES)
    assert results[0].is_recommended is True
    for r in results[1:]:
        assert r.is_recommended is False


def test_score_is_within_valid_range():
    results = score_suppliers(SAMPLE_QUOTES)
    for r in results:
        assert 0.0 <= r.score <= 100.0


def test_score_breakdown_sums_to_total():
    results = score_suppliers(SAMPLE_QUOTES)
    for r in results:
        bd = r.breakdown
        computed = bd.price + bd.delivery + bd.quality + bd.historical + bd.payment_terms + bd.availability + bd.risk
        assert abs(computed - r.score) < 0.01


def test_reasons_list_not_empty():
    results = score_suppliers(SAMPLE_QUOTES)
    for r in results:
        assert isinstance(r.reasons, list)
        assert len(r.reasons) > 0


def test_recommended_has_prefix_in_reasons():
    results = score_suppliers(SAMPLE_QUOTES)
    assert any("Recommended" in r or "Best" in r for r in results[0].reasons)


def test_empty_quotes_returns_empty():
    assert score_suppliers([]) == []


def test_single_quote_always_recommended():
    results = score_suppliers([SAMPLE_QUOTES[0]])
    assert len(results) == 1
    assert results[0].is_recommended is True


def test_high_risk_reason_appears():
    high_risk_quote = [{**SAMPLE_QUOTES[0], "risk_score": 80.0}]
    results = score_suppliers(high_risk_quote)
    assert any("risk" in r.lower() for r in results[0].reasons)


# ---------------------------------------------------------------------------
# Explanation generator tests
# ---------------------------------------------------------------------------

def test_generate_explanation_contains_supplier_name():
    results = score_suppliers([SAMPLE_QUOTES[0]])
    explanation = generate_explanation(results[0])
    assert "Alpha Chemicals" in explanation


def test_generate_explanation_contains_score():
    results = score_suppliers([SAMPLE_QUOTES[0]])
    explanation = generate_explanation(results[0])
    assert "Overall Score" in explanation


def test_generate_explanation_contains_breakdown():
    results = score_suppliers([SAMPLE_QUOTES[0]])
    explanation = generate_explanation(results[0])
    assert "Price" in explanation
    assert "Delivery" in explanation
    assert "Quality" in explanation


# ---------------------------------------------------------------------------
# ScoreBreakdown total property
# ---------------------------------------------------------------------------

def test_score_breakdown_total():
    bd = ScoreBreakdown(
        price=20.0, delivery=15.0, quality=10.0,
        historical=12.0, payment_terms=8.0, availability=4.0, risk=3.0
    )
    assert bd.total == 72.0


def test_score_breakdown_to_dict_has_all_keys():
    bd = ScoreBreakdown()
    d = bd.to_dict()
    expected_keys = ["price", "delivery", "quality", "historical", "payment_terms", "availability", "risk", "total"]
    for k in expected_keys:
        assert k in d
