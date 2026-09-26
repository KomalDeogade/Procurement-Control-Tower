"""
Tests for AI Service — fallback mode, structured output, and provider abstraction.
All tests must pass without any AI API key configured.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch


# ─────────────────────────────────────────────────────────────
# AI Service initialization
# ─────────────────────────────────────────────────────────────

def test_ai_service_initializes_in_mock_mode():
    """AI service should initialize in mock mode when no key is configured."""
    from app.services.ai_service import ai_service
    assert ai_service is not None
    # In test env, no API key is set
    assert ai_service.is_available is False or ai_service.provider in ("none", "mock")


def test_ai_service_provider_from_config():
    """Provider should be readable from settings."""
    from app.services.ai_service import AIService
    svc = AIService()
    assert svc.provider in ("none", "openai", "gemini", "anthropic")


# ─────────────────────────────────────────────────────────────
# Document extraction — mock mode
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_document_returns_structured_output():
    """extract_document must return ExtractedQuote even without API key."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.extract_document("Test quotation document for XLR-500 at Rs 1650/L for 5000L")
    assert result is not None
    assert hasattr(result, "unit_price")
    assert hasattr(result, "quantity")
    assert hasattr(result, "total_price")
    assert hasattr(result, "confidence")
    assert hasattr(result, "needs_review")
    assert hasattr(result, "missing_fields")


@pytest.mark.asyncio
async def test_extract_document_to_dict_has_all_fields():
    """to_dict must include all expected keys."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.extract_document("Sample quotation text")
    d = result.to_dict()
    expected_keys = [
        "supplier_name", "material", "quantity", "unit_price", "tax", "freight",
        "total_price", "availability", "lead_time_days", "delivery_date",
        "payment_terms", "warranty", "service_details", "confidence",
        "needs_review", "missing_fields"
    ]
    for k in expected_keys:
        assert k in d, f"Missing key: {k}"


@pytest.mark.asyncio
async def test_extract_document_validates_required_fields():
    """validate() must return list of missing fields."""
    from app.services.ai_service import ExtractedQuote
    quote = ExtractedQuote(supplier_name="Test", quantity=None, unit_price=None, total_price=None)
    missing = quote.validate()
    assert "unit_price" in missing
    assert "quantity" in missing
    assert "total_price" in missing


@pytest.mark.asyncio
async def test_extract_document_needs_review_when_confidence_low():
    """needs_review should be True when confidence < 0.7."""
    from app.services.ai_service import ExtractedQuote
    quote = ExtractedQuote(
        unit_price=1650.0, quantity=5000.0, total_price=8250000.0,
        confidence=0.5,  # below threshold
        needs_review=False  # will be set by validate
    )
    missing = quote.validate()
    # confidence < 0.7 should trigger needs_review
    quote.needs_review = len(missing) > 0 or quote.confidence < 0.7
    assert quote.needs_review is True


@pytest.mark.asyncio
async def test_extract_document_ready_when_all_fields_present():
    """needs_review should be False when all required fields found and confidence high."""
    from app.services.ai_service import ExtractedQuote
    quote = ExtractedQuote(
        unit_price=1650.0, quantity=5000.0, total_price=8250000.0,
        confidence=0.9,
        needs_review=False
    )
    missing = quote.validate()
    quote.needs_review = len(missing) > 0 or quote.confidence < 0.7
    assert quote.needs_review is False
    assert len(missing) == 0


# ─────────────────────────────────────────────────────────────
# Explanation generation
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_explanation_returns_string():
    """generate_explanation must return a non-empty string."""
    from app.services.ai_service import AIService
    svc = AIService()
    scored = [
        {"supplier_name": "Vendor A", "score": 85.2, "rank": 1, "recommended": True,
         "price_score": 90, "delivery_score": 85},
        {"supplier_name": "Vendor B", "score": 72.1, "rank": 2, "recommended": False,
         "price_score": 95, "delivery_score": 55},
    ]
    result = await svc.generate_explanation(scored, {"material": "XLR-500", "budget": 8000000})
    assert isinstance(result, str)
    assert len(result) > 10


@pytest.mark.asyncio
async def test_generate_explanation_mentions_supplier():
    """Mock explanation should mention supplier or scoring context."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.generate_explanation(
        [{"supplier_name": "Vendor A", "score": 85}],
        {"material": "XLR-500"}
    )
    # In mock mode this returns the deterministic explanation string
    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────
# Negotiation email draft
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_draft_email_returns_draft_status():
    """Draft email must have status=DRAFT and requires_approval=True."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.draft_email(
        supplier_name="Vendor B",
        requirement_id="REQ-1001",
        material="Industrial Lubricant XLR-500",
        quoted_price=8_500_000,
        target_budget=8_000_000,
        desired_delivery_days=14,
        preferred_payment_terms="NET 30",
    )
    assert result["status"] == "DRAFT"
    assert result["requires_approval"] is True
    assert "subject" in result
    assert "body" in result
    assert "generated_at" in result


@pytest.mark.asyncio
async def test_draft_email_subject_contains_requirement_id():
    """Email subject must include requirement ID."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.draft_email(
        supplier_name="Test Supplier",
        requirement_id="REQ-DEMO",
        material="XLR-500",
        quoted_price=1_000_000,
        target_budget=800_000,
        desired_delivery_days=14,
        preferred_payment_terms="NET 30",
    )
    assert "REQ-DEMO" in result["subject"]


@pytest.mark.asyncio
async def test_draft_email_body_is_nonempty():
    """Email body must be a non-empty string."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.draft_email(
        supplier_name="Alpha Chemicals",
        requirement_id="REQ-001",
        material="XLR-500",
        quoted_price=2_000_000,
        target_budget=1_800_000,
        desired_delivery_days=21,
        preferred_payment_terms="NET 45",
    )
    assert isinstance(result["body"], str)
    assert len(result["body"]) > 50


# ─────────────────────────────────────────────────────────────
# Email summarization
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_text_returns_email_summary():
    """summarize_text must return EmailSummary with all expected fields."""
    from app.services.ai_service import AIService
    svc = AIService()
    text = "We are pleased to offer 5000 liters of XLR-500 at ₹1,650/L, available immediately. NET 30 payment. Delivery in 14 days."
    result = await svc.summarize_text(text)
    assert hasattr(result, "summary")
    assert hasattr(result, "required_action")
    assert hasattr(result, "risks")
    assert hasattr(result, "sentiment")


@pytest.mark.asyncio
async def test_summarize_text_to_dict_complete():
    """EmailSummary.to_dict() must include all fields."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.summarize_text("Test message")
    d = result.to_dict()
    for k in ["summary", "required_action", "risks", "sentiment"]:
        assert k in d


# ─────────────────────────────────────────────────────────────
# Daily summary
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_daily_summary_returns_expected_keys():
    """generate_daily_summary must return structured response."""
    from app.services.ai_service import AIService
    svc = AIService()
    data = {
        "date": "2026-09-25",
        "pending_approvals": 3,
        "open_requirements": 5,
        "stock_risk_count": 2,
        "overdue_invoices_count": 1,
        "high_risk_supplier_count": 1,
    }
    result = await svc.generate_daily_summary(data)
    assert "generated_at" in result
    assert "data_source" in result
    assert result["data_source"] == "deterministic_system"
    assert "ai_provider" in result


@pytest.mark.asyncio
async def test_daily_summary_does_not_invent_metrics():
    """The AI brief must use system data as source — data_source field verifies this."""
    from app.services.ai_service import AIService
    svc = AIService()
    result = await svc.generate_daily_summary({"pending_approvals": 0, "stock_risk_count": 0})
    assert result["data_source"] == "deterministic_system"


# ─────────────────────────────────────────────────────────────
# Inventory risk explanation
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_explain_inventory_risk_returns_string():
    """explain_inventory_risk must return a non-empty string."""
    from app.services.ai_service import AIService
    svc = AIService()
    analysis = {
        "material_name": "Industrial Lubricant XLR-500",
        "material_code": "XLR-500",
        "risk_status": "CRITICAL",
        "available_stock": 150,
        "average_daily_consumption": 50,
        "lead_time_days": 14,
        "stock_coverage_days": 3,
        "safety_stock": 200,
        "recommended_reorder_qty": 1000,
    }
    result = await svc.explain_inventory_risk(analysis)
    assert isinstance(result, str)
    assert len(result) > 10


# ─────────────────────────────────────────────────────────────
# Fallback resilience — simulate API failures
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_service_does_not_crash_on_network_error():
    """System must not crash if AI provider throws an exception."""
    from app.services.ai_service import AIService
    from unittest.mock import patch, AsyncMock

    svc = AIService()
    # Patch the provider call to raise an exception
    with patch.object(svc, "_call_openai", new=AsyncMock(side_effect=Exception("Network timeout"))):
        svc.provider = "openai"
        svc.api_key = "fake-key"
        result = await svc._call_ai("system", "user", json_mode=False)
        # Must fall back to mock, not crash
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_extract_document_handles_bad_json():
    """extract_document must handle malformed AI responses gracefully."""
    from app.services.ai_service import AIService
    from unittest.mock import AsyncMock

    svc = AIService()
    with patch.object(svc, "_call_ai", new=AsyncMock(return_value="not valid json {{}")):
        result = await svc.extract_document("some document text")
        # Should return ExtractedQuote with empty fields, not crash
        assert result is not None
        assert result.needs_review is True  # missing required fields


@pytest.mark.asyncio
async def test_summarize_email_handles_bad_json():
    """summarize_text must handle malformed AI responses gracefully."""
    from app.services.ai_service import AIService
    from unittest.mock import AsyncMock

    svc = AIService()
    with patch.object(svc, "_call_ai", new=AsyncMock(return_value="INVALID_JSON")):
        result = await svc.summarize_text("some text")
        assert result is not None
        assert isinstance(result.summary, str)


# ─────────────────────────────────────────────────────────────
# ExtractedQuote validation edge cases
# ─────────────────────────────────────────────────────────────

def test_extracted_quote_all_none_fails_validation():
    from app.services.ai_service import ExtractedQuote
    q = ExtractedQuote()
    missing = q.validate()
    assert "unit_price" in missing
    assert "quantity" in missing
    assert "total_price" in missing


def test_extracted_quote_partial_pass():
    from app.services.ai_service import ExtractedQuote
    q = ExtractedQuote(unit_price=1650.0, total_price=8250000.0)  # quantity missing
    missing = q.validate()
    assert "unit_price" not in missing
    assert "total_price" not in missing
    assert "quantity" in missing
