"""
Provider-agnostic AI Service — SCM Procurement Control Tower.

Design principles:
  • The AI layer is advisory only — it NEVER makes business decisions.
  • Deterministic engines (scoring, 3-way match, inventory) remain the source of truth.
  • When no API key is available the service returns deterministic mock responses
    so the system can run fully offline for development/demo.
  • Adding a new provider only requires adding a new _call_<provider> method.

Configuration (environment variables):
    AI_PROVIDER   = "openai" | "gemini" | "anthropic" | "none"  (default: "none")
    AI_API_KEY    = <key>
    AI_MODEL      = gpt-4o-mini | gemini-1.5-flash | claude-3-haiku-20240307 | ...
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Data-classes for typed AI outputs
# ──────────────────────────────────────────────────────────────

class ExtractedQuote:
    """Structured output of AI document extraction."""
    def __init__(self, **kwargs):
        self.supplier_name: Optional[str] = kwargs.get("supplier_name")
        self.material: Optional[str] = kwargs.get("material")
        self.quantity: Optional[float] = kwargs.get("quantity")
        self.unit_price: Optional[float] = kwargs.get("unit_price")
        self.tax: Optional[float] = kwargs.get("tax", 0.0)
        self.freight: Optional[float] = kwargs.get("freight", 0.0)
        self.total_price: Optional[float] = kwargs.get("total_price")
        self.availability: Optional[str] = kwargs.get("availability")
        self.lead_time_days: Optional[int] = kwargs.get("lead_time_days")
        self.delivery_date: Optional[str] = kwargs.get("delivery_date")
        self.payment_terms: Optional[str] = kwargs.get("payment_terms")
        self.warranty: Optional[str] = kwargs.get("warranty")
        self.service_details: Optional[str] = kwargs.get("service_details")
        self.confidence: float = kwargs.get("confidence", 0.0)
        self.needs_review: bool = kwargs.get("needs_review", True)
        self.missing_fields: list[str] = kwargs.get("missing_fields", [])
        self.raw_text: Optional[str] = kwargs.get("raw_text")

    def validate(self) -> list[str]:
        """Return list of missing required fields."""
        required = ["unit_price", "total_price", "quantity"]
        return [f for f in required if getattr(self, f) is None]

    def to_dict(self) -> dict:
        return {
            "supplier_name": self.supplier_name,
            "material": self.material,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "tax": self.tax,
            "freight": self.freight,
            "total_price": self.total_price,
            "availability": self.availability,
            "lead_time_days": self.lead_time_days,
            "delivery_date": self.delivery_date,
            "payment_terms": self.payment_terms,
            "warranty": self.warranty,
            "service_details": self.service_details,
            "confidence": self.confidence,
            "needs_review": self.needs_review,
            "missing_fields": self.missing_fields,
        }


class EmailSummary:
    """Structured output of AI email summarization."""
    def __init__(self, **kwargs):
        self.summary: str = kwargs.get("summary", "")
        self.price_mentioned: Optional[str] = kwargs.get("price_mentioned")
        self.availability: Optional[str] = kwargs.get("availability")
        self.delivery: Optional[str] = kwargs.get("delivery")
        self.payment_terms: Optional[str] = kwargs.get("payment_terms")
        self.risks: list[str] = kwargs.get("risks", [])
        self.required_action: str = kwargs.get("required_action", "Review")
        self.sentiment: str = kwargs.get("sentiment", "neutral")

    def to_dict(self) -> dict:
        return self.__dict__


# ──────────────────────────────────────────────────────────────
# Main AI Service
# ──────────────────────────────────────────────────────────────

class AIService:
    """
    Provider-agnostic AI service with graceful fallback.

    Usage:
        from app.services.ai_service import ai_service
        explanation = await ai_service.generate_explanation(scores, context)
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL
        self._client = None

        if self.provider == "none" or not self.api_key:
            logger.info("AI Service: running in MOCK/FALLBACK mode (no API key configured)")
        else:
            logger.info(f"AI Service: using provider={self.provider}, model={self.model}")

    @property
    def is_available(self) -> bool:
        return self.provider != "none" and bool(self.api_key)

    # ── Core dispatcher ──────────────────────────────────────

    async def _call_ai(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """
        Dispatch to the configured provider.
        Falls back to mock if unavailable.
        """
        if not self.is_available:
            return self._mock_response(system_prompt, user_prompt, json_mode)

        try:
            if self.provider == "openai":
                return await self._call_openai(system_prompt, user_prompt, json_mode)
            elif self.provider in ("gemini", "google"):
                return await self._call_gemini(system_prompt, user_prompt, json_mode)
            elif self.provider == "anthropic":
                return await self._call_anthropic(system_prompt, user_prompt, json_mode)
            else:
                logger.warning(f"Unknown AI provider: {self.provider}. Using mock.")
                return self._mock_response(system_prompt, user_prompt, json_mode)
        except Exception as exc:
            logger.error(f"AI call failed ({self.provider}): {exc}. Using fallback.")
            return self._mock_response(system_prompt, user_prompt, json_mode)

    # ── OpenAI ───────────────────────────────────────────────

    async def _call_openai(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError:
            logger.warning("openai package not installed. Falling back to mock.")
            return self._mock_response(system_prompt, user_prompt, json_mode)

        client = AsyncOpenAI(api_key=self.api_key)
        model = self.model or "gpt-4o-mini"
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ── Google Gemini ─────────────────────────────────────────

    async def _call_gemini(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            logger.warning("google-generativeai not installed. Falling back to mock.")
            return self._mock_response(system_prompt, user_prompt, json_mode)

        genai.configure(api_key=self.api_key)
        model = self.model or "gemini-1.5-flash"
        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
        )
        prompt = user_prompt
        if json_mode:
            prompt += "\n\nIMPORTANT: Respond with valid JSON only."

        response = gen_model.generate_content(prompt)
        return response.text or ""

    # ── Anthropic Claude ──────────────────────────────────────

    async def _call_anthropic(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        try:
            import anthropic  # type: ignore
        except ImportError:
            logger.warning("anthropic package not installed. Falling back to mock.")
            return self._mock_response(system_prompt, user_prompt, json_mode)

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        model = self.model or "claude-3-haiku-20240307"
        prompt = user_prompt
        if json_mode:
            prompt += "\n\nIMPORTANT: Respond with valid JSON only, no markdown."

        message = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text if message.content else ""

    # ── Mock / Fallback ───────────────────────────────────────

    def _mock_response(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        """
        Deterministic mock responses for development/demo.
        Returns plausible structured output without any AI API calls.
        """
        prompt_lower = user_prompt.lower()

        if json_mode:
            # Document extraction mock
            if "extract" in prompt_lower or "quotation" in prompt_lower or "document" in prompt_lower:
                return json.dumps({
                    "supplier_name": "Demo Supplier Co.",
                    "material": "Industrial Lubricant XLR-500",
                    "quantity": 5000,
                    "unit_price": 1650.0,
                    "tax": 148500.0,
                    "freight": 25000.0,
                    "total_price": 8398500.0,
                    "availability": "In Stock",
                    "lead_time_days": 14,
                    "delivery_date": None,
                    "payment_terms": "NET 30",
                    "warranty": "12 months",
                    "service_details": "Technical support included",
                    "confidence": 0.82,
                    "needs_review": False,
                    "missing_fields": []
                })
            # Email summarization mock
            elif "summarize" in prompt_lower or "email" in prompt_lower or "supplier" in prompt_lower:
                return json.dumps({
                    "summary": "[MOCK] Supplier confirms availability of requested material. Competitive pricing offered.",
                    "price_mentioned": "₹1,650/unit",
                    "availability": "In Stock",
                    "delivery": "14 days",
                    "payment_terms": "NET 30",
                    "risks": ["Single-source dependency", "Lead time may extend during peak"],
                    "required_action": "Verify pricing against market rates and proceed with RFQ.",
                    "sentiment": "positive"
                })
            # Daily summary mock
            elif "daily" in prompt_lower or "brief" in prompt_lower or "morning" in prompt_lower:
                return json.dumps({
                    "greeting": "Good Morning",
                    "brief": "[MOCK AI BRIEF] 3 items require your attention today.",
                    "critical_items": [],
                    "recommended_actions": [
                        "Review pending approvals",
                        "Check stock risk items",
                        "Review overdue invoices"
                    ]
                })
            else:
                return json.dumps({"response": "[MOCK AI] No AI provider configured. Using deterministic fallback."})
        else:
            # Plain text responses
            if "negotiat" in prompt_lower or "email" in prompt_lower or "draft" in prompt_lower:
                return self._mock_negotiation_email(user_prompt)
            elif "explain" in prompt_lower or "score" in prompt_lower or "recommend" in prompt_lower:
                return self._mock_explanation(user_prompt)
            elif "inventory" in prompt_lower or "stock" in prompt_lower:
                return "[MOCK] Based on current consumption rates and safety stock levels, this material requires immediate attention. Consider initiating a replenishment order."
            else:
                return "[MOCK AI] AI provider not configured. This is a deterministic placeholder response."

    def _mock_negotiation_email(self, prompt: str) -> str:
        return """Subject: Request for Revised Commercial Offer

Dear Supplier,

Thank you for your quotation. We appreciate your competitive offer.

After reviewing your proposal against our budget and project requirements, we would like to request a revision of the following terms:

1. PRICING: We request a reduction of 5-8% to align with our approved budget.
2. DELIVERY: Our project timeline requires delivery within 14 days of PO issuance.
3. PAYMENT TERMS: We propose NET 45 days from invoice date.
4. QUALITY ASSURANCE: Please include material test certificates with delivery.

We value a long-term partnership and believe these terms are mutually beneficial.

Please revert with your best commercial offer by [DATE].

[NOTE: This is a draft email. Review and approve before sending.]

Best regards,
Procurement Team
SCM Control Tower"""

    def _mock_explanation(self, prompt: str) -> str:
        return (
            "[MOCK AI Explanation] The deterministic scoring engine has ranked suppliers based on "
            "weighted criteria: Price (30%), Delivery (20%), Quality (15%), Historical Performance (15%), "
            "Payment Terms (10%), Availability (5%), and Risk (5%). "
            "The recommended supplier scored highest primarily due to competitive pricing, "
            "reliable delivery track record, and strong quality compliance. "
            "Note: This explanation is AI-generated based on verified system data — "
            "the underlying scores are calculated deterministically."
        )

    # ═══════════════════════════════════════════════════════════
    # Public API Methods
    # ═══════════════════════════════════════════════════════════

    async def extract_document(self, document_text: str, context: dict | None = None) -> ExtractedQuote:
        """
        Extract structured quote fields from raw document text.
        The AI returns JSON; we validate it before creating a quote.
        """
        system_prompt = """You are a procurement document parser. Extract supplier quotation fields from the provided text.
Return ONLY valid JSON with these exact fields (use null if not found):
supplier_name, material, quantity (number), unit_price (number), tax (number), freight (number),
total_price (number), availability (string), lead_time_days (number), delivery_date (ISO date string or null),
payment_terms (string), warranty (string), service_details (string), confidence (0-1 float).
Do NOT invent values. If a field is unclear, set it to null."""

        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context)}"

        user_prompt = f"Extract quotation data from this document:{context_str}\n\n---\n{document_text}\n---"

        raw = await self._call_ai(system_prompt, user_prompt, json_mode=True)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("AI extraction returned non-JSON. Using empty result.")
            data = {}

        quote = ExtractedQuote(**data)
        missing = quote.validate()
        quote.missing_fields = missing
        quote.needs_review = len(missing) > 0 or quote.confidence < 0.7
        quote.raw_text = document_text[:500]

        return quote

    async def generate_explanation(self, scored_suppliers: list[dict], requirement_context: dict | None = None) -> str:
        """
        Generate a human-readable explanation of supplier ranking.
        The AI receives pre-computed scores — it does NOT re-calculate them.
        """
        system_prompt = """You are a procurement analyst assistant. Your role is to explain pre-calculated 
supplier scores in plain business language. You must NOT recalculate or question the scores — 
they were computed by a deterministic engine. Explain WHY the ranking makes sense in 2-3 concise paragraphs.
Focus on the top 2-3 differentiating factors."""

        scored_text = json.dumps(scored_suppliers[:5], indent=2)
        context_text = json.dumps(requirement_context or {}, indent=2)

        user_prompt = f"""Explain this supplier ranking to a procurement manager:

Requirement Context:
{context_text}

Pre-calculated Supplier Scores:
{scored_text}

Write a clear, factual explanation of why suppliers are ranked in this order."""

        return await self._call_ai(system_prompt, user_prompt, json_mode=False)

    async def draft_email(
        self,
        supplier_name: str,
        requirement_id: str,
        material: str,
        quoted_price: float,
        target_budget: float,
        desired_delivery_days: int,
        preferred_payment_terms: str,
        additional_context: str = "",
    ) -> dict:
        """
        Draft a supplier negotiation email. Returns a DRAFT — user must approve before sending.
        """
        system_prompt = """You are a professional procurement manager. Write a polite but firm 
negotiation email to a supplier requesting improved commercial terms. 
The email must be professional, specific, and include a clear call to action.
Include [DRAFT - REQUIRES APPROVAL BEFORE SENDING] at the top."""

        gap_pct = round(((quoted_price - target_budget) / target_budget) * 100, 1) if target_budget > 0 else 0

        user_prompt = f"""Draft a negotiation email with these parameters:
Supplier: {supplier_name}
Requirement ID: {requirement_id}
Material: {material}
Supplier's Quoted Price: ₹{quoted_price:,.2f}
Our Target Budget: ₹{target_budget:,.2f}
Price Gap: {gap_pct}% above budget
Desired Delivery: {desired_delivery_days} days
Preferred Payment Terms: {preferred_payment_terms}
Additional Context: {additional_context or 'None'}"""

        body = await self._call_ai(system_prompt, user_prompt, json_mode=False)

        return {
            "subject": f"Request for Revised Commercial Offer — {requirement_id}",
            "to": supplier_name,
            "body": body,
            "status": "DRAFT",
            "requires_approval": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ai_provider": self.provider if self.is_available else "mock",
        }

    async def summarize_text(self, text: str, context: str = "") -> EmailSummary:
        """
        Summarize a supplier email/message into structured procurement-relevant fields.
        """
        system_prompt = """You are a procurement assistant. Summarize supplier communications.
Return ONLY valid JSON with these fields:
summary (string), price_mentioned (string or null), availability (string or null),
delivery (string or null), payment_terms (string or null), 
risks (list of strings), required_action (string), sentiment (positive/neutral/negative/concerning)."""

        user_prompt = f"Summarize this supplier communication for a procurement manager:\n{context}\n---\n{text}"

        raw = await self._call_ai(system_prompt, user_prompt, json_mode=True)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {
                "summary": text[:200],
                "required_action": "Manual review required",
                "risks": [],
                "sentiment": "neutral"
            }

        return EmailSummary(**data)

    async def generate_daily_summary(self, data: dict) -> dict:
        """
        Generate a daily AI procurement brief from verified system data.
        The AI summarizes — it does NOT invent metrics.
        All numbers come from the deterministic system.
        """
        system_prompt = """You are a procurement intelligence system. Generate a concise daily brief 
for a procurement manager. Use ONLY the data provided — never invent metrics.
Return JSON with: greeting (string), executive_summary (string, 2 sentences),
critical_items (list of strings), recommended_actions (list of strings, max 5)."""

        user_prompt = f"""Generate today's procurement brief from this verified system data:
{json.dumps(data, indent=2, default=str)}"""

        raw = await self._call_ai(system_prompt, user_prompt, json_mode=True)

        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            result = {
                "greeting": "Good Morning",
                "executive_summary": f"You have {data.get('pending_approvals', 0)} pending approvals and {data.get('stock_risk', 0)} stock risk items requiring attention.",
                "critical_items": [],
                "recommended_actions": ["Review pending approvals", "Check stock risk items"],
            }

        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["data_source"] = "deterministic_system"
        result["ai_provider"] = self.provider if self.is_available else "mock"
        return result

    async def explain_inventory_risk(self, analysis: dict) -> str:
        """
        Generate a plain-language explanation of an inventory risk.
        The calculation is deterministic; AI only explains it.
        """
        system_prompt = """You are a supply chain analyst. Explain inventory risk in plain language.
Focus on: why there is risk, what's causing it, and what action to take.
Be concise (3-4 sentences). Use business language, not technical jargon."""

        user_prompt = f"""Explain this inventory risk to a procurement manager:
Material: {analysis.get('material_name')} ({analysis.get('material_code')})
Risk Status: {analysis.get('risk_status')}
Available Stock: {analysis.get('available_stock')} units
Daily Consumption: {analysis.get('average_daily_consumption')} units/day
Lead Time: {analysis.get('lead_time_days')} days
Coverage: {analysis.get('stock_coverage_days')} days
Safety Stock: {analysis.get('safety_stock')} units
Recommended Reorder: {analysis.get('recommended_reorder_qty')} units"""

        return await self._call_ai(system_prompt, user_prompt, json_mode=False)


# ── Singleton ─────────────────────────────────────────────────
ai_service = AIService()
