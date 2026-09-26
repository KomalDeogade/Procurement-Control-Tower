"""
Supplier Scoring Service – deterministic scoring engine.

Default configurable weights:
  Price              30%
  Delivery           20%
  Quality            15%
  Historical         15%
  Payment Terms      10%
  Availability        5%
  Risk                5%

NO LLM used. All calculations are pure Python math.
"""

from dataclasses import dataclass, field


@dataclass
class ScoreBreakdown:
    price: float = 0.0
    delivery: float = 0.0
    quality: float = 0.0
    historical: float = 0.0
    payment_terms: float = 0.0
    availability: float = 0.0
    risk: float = 0.0

    @property
    def total(self) -> float:
        return round(
            self.price + self.delivery + self.quality + self.historical
            + self.payment_terms + self.availability + self.risk, 2
        )

    def to_dict(self) -> dict:
        return {
            "price": self.price,
            "delivery": self.delivery,
            "quality": self.quality,
            "historical": self.historical,
            "payment_terms": self.payment_terms,
            "availability": self.availability,
            "risk": self.risk,
            "total": self.total,
        }


@dataclass
class ScoredSupplier:
    supplier_id: int
    supplier_name: str
    score: float
    breakdown: ScoreBreakdown
    reasons: list[str] = field(default_factory=list)
    is_recommended: bool = False

    def to_dict(self) -> dict:
        return {
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "score": self.score,
            "breakdown": self.breakdown.to_dict(),
            "reasons": self.reasons,
            "is_recommended": self.is_recommended,
        }


# Default weights (configurable)
DEFAULT_WEIGHTS = {
    "price": 0.30,
    "delivery": 0.20,
    "quality": 0.15,
    "historical": 0.15,
    "payment_terms": 0.10,
    "availability": 0.05,
    "risk": 0.05,
}

# Payment terms scoring (lower is better for buyer)
PAYMENT_TERMS_SCORES = {
    "NET 60": 100,
    "NET 45": 85,
    "NET 30": 70,
    "NET 15": 50,
    "ADVANCE": 20,
    "COD": 30,
}


def _normalize_price_score(prices: list[float], current_price: float) -> float:
    """Lower price = higher score. Returns 0-100."""
    if not prices or current_price <= 0:
        return 0.0
    min_price = min(prices)
    max_price = max(prices)
    if max_price == min_price:
        return 100.0
    # Inverse: lowest price gets 100
    return round(((max_price - current_price) / (max_price - min_price)) * 100, 2)


def _normalize_delivery_score(lead_times: list[int], current_lead: int) -> float:
    """Shorter lead time = higher score. Returns 0-100."""
    if not lead_times or current_lead <= 0:
        return 50.0
    min_lead = min(lead_times)
    max_lead = max(lead_times)
    if max_lead == min_lead:
        return 100.0
    return round(((max_lead - current_lead) / (max_lead - min_lead)) * 100, 2)


def _normalize_availability_score(availability: str | None) -> float:
    """Convert availability text to score."""
    if not availability:
        return 50.0
    avail_lower = availability.lower()
    if "immediate" in avail_lower or "in stock" in avail_lower:
        return 100.0
    elif "1 week" in avail_lower or "7 day" in avail_lower:
        return 85.0
    elif "2 week" in avail_lower or "14 day" in avail_lower:
        return 70.0
    elif "3 week" in avail_lower or "21 day" in avail_lower:
        return 55.0
    elif "1 month" in avail_lower or "30 day" in avail_lower:
        return 40.0
    else:
        return 50.0


def _normalize_payment_terms_score(terms: str | None) -> float:
    """Score payment terms. Longer terms = better for buyer."""
    if not terms:
        return 50.0
    terms_upper = terms.upper().strip()
    for key, score in PAYMENT_TERMS_SCORES.items():
        if key in terms_upper:
            return float(score)
    return 50.0


def score_suppliers(
    quotes: list[dict],
    weights: dict | None = None,
) -> list[ScoredSupplier]:
    """
    Score multiple supplier quotes and return ranked results.

    Each quote dict should have:
        supplier_id, supplier_name, unit_price, total_price, quantity,
        lead_time_days, availability, payment_terms, quality_score,
        delivery_score, risk_score, warranty
    """
    if not quotes:
        return []

    w = weights or DEFAULT_WEIGHTS

    # Collect all prices and lead times for normalization
    all_total_prices = [q.get("total_price", 0) for q in quotes if q.get("total_price", 0) > 0]
    all_lead_times = [q.get("lead_time_days", 30) for q in quotes if q.get("lead_time_days")]

    results: list[ScoredSupplier] = []

    for q in quotes:
        reasons: list[str] = []
        breakdown = ScoreBreakdown()

        # Price score (30%)
        total_price = q.get("total_price", 0)
        raw_price = _normalize_price_score(all_total_prices, total_price)
        breakdown.price = round(raw_price * w["price"], 2)
        if raw_price >= 80:
            reasons.append("Competitive pricing")
        elif raw_price <= 30:
            reasons.append("Above-average pricing")

        # Delivery score (20%)
        lead_time = q.get("lead_time_days", 30)
        raw_delivery = _normalize_delivery_score(all_lead_times, lead_time)
        supplier_delivery = q.get("delivery_score", 70.0)
        combined_delivery = (raw_delivery * 0.5) + (supplier_delivery * 0.5)
        breakdown.delivery = round(combined_delivery * w["delivery"], 2)
        if combined_delivery >= 80:
            reasons.append("Excellent delivery performance")
        elif combined_delivery <= 40:
            reasons.append("Delivery concerns")

        # Quality score (15%)
        quality = q.get("quality_score", 70.0)
        breakdown.quality = round(quality * w["quality"], 2)
        if quality >= 85:
            reasons.append("High quality rating")
        elif quality <= 50:
            reasons.append("Quality concerns")

        # Historical performance (15%)
        historical = q.get("historical_performance", 70.0)
        breakdown.historical = round(historical * w["historical"], 2)
        if historical >= 85:
            reasons.append("Strong historical performance")

        # Payment terms (10%)
        pt_score = _normalize_payment_terms_score(q.get("payment_terms"))
        breakdown.payment_terms = round(pt_score * w["payment_terms"], 2)
        if pt_score >= 80:
            reasons.append("Favorable payment terms")

        # Availability (5%)
        avail_score = _normalize_availability_score(q.get("availability"))
        breakdown.availability = round(avail_score * w["availability"], 2)
        if avail_score >= 85:
            reasons.append("Immediate availability")

        # Risk (5%) – lower risk_score = better
        risk = q.get("risk_score", 50.0)
        risk_inverted = max(0, 100 - risk)
        breakdown.risk = round(risk_inverted * w["risk"], 2)
        if risk >= 70:
            reasons.append("⚠ High supplier risk")
        elif risk <= 20:
            reasons.append("Low risk profile")

        total = breakdown.total

        results.append(ScoredSupplier(
            supplier_id=q.get("supplier_id", 0),
            supplier_name=q.get("supplier_name", "Unknown"),
            score=total,
            breakdown=breakdown,
            reasons=reasons,
        ))

    # Sort by score descending
    results.sort(key=lambda s: s.score, reverse=True)

    # Mark top scorer as recommended
    if results:
        results[0].is_recommended = True
        results[0].reasons.insert(0, "★ Recommended: Best overall score")

    return results


def generate_explanation(scored: ScoredSupplier) -> str:
    """Generate a human-readable explanation from deterministic reasons."""
    lines = [f"Supplier: {scored.supplier_name}"]
    lines.append(f"Overall Score: {scored.score}/100")
    lines.append("")
    lines.append("Score Breakdown:")
    bd = scored.breakdown
    lines.append(f"  Price: {bd.price} (max 30)")
    lines.append(f"  Delivery: {bd.delivery} (max 20)")
    lines.append(f"  Quality: {bd.quality} (max 15)")
    lines.append(f"  Historical: {bd.historical} (max 15)")
    lines.append(f"  Payment Terms: {bd.payment_terms} (max 10)")
    lines.append(f"  Availability: {bd.availability} (max 5)")
    lines.append(f"  Risk: {bd.risk} (max 5)")
    lines.append("")
    if scored.reasons:
        lines.append("Key Factors:")
        for r in scored.reasons:
            lines.append(f"  • {r}")
    return "\n".join(lines)
