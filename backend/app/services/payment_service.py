"""
Payment due monitoring service – deterministic calculations.

Calculates due dates from Invoice Date + Payment Terms.
Supports: 15, 30, 45, 60 days.
"""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


@dataclass
class PaymentDueInfo:
    invoice_id: str
    supplier_name: str
    amount: float
    invoice_date: str
    payment_terms_days: int
    due_date: str
    days_until_due: int
    category: str  # DUE_TODAY, DUE_1_3_DAYS, DUE_4_7_DAYS, DUE_LATER, OVERDUE
    is_overdue: bool

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "supplier_name": self.supplier_name,
            "amount": self.amount,
            "invoice_date": self.invoice_date,
            "payment_terms_days": self.payment_terms_days,
            "due_date": self.due_date,
            "days_until_due": self.days_until_due,
            "category": self.category,
            "is_overdue": self.is_overdue,
        }


def parse_payment_terms_days(terms: str | None) -> int:
    """Extract number of days from payment terms string."""
    if not terms:
        return 30  # default
    terms_upper = terms.upper().strip()
    for days in [60, 45, 30, 15]:
        if str(days) in terms_upper:
            return days
    if "ADVANCE" in terms_upper or "COD" in terms_upper:
        return 0
    return 30


def calculate_due_date(invoice_date: datetime, payment_terms: str | None) -> datetime:
    """Calculate payment due date from invoice date + terms."""
    days = parse_payment_terms_days(payment_terms)
    return invoice_date + timedelta(days=days)


def categorize_payment(days_until_due: int) -> str:
    """Categorize payment by urgency."""
    if days_until_due < 0:
        return "OVERDUE"
    elif days_until_due == 0:
        return "DUE_TODAY"
    elif days_until_due <= 3:
        return "DUE_1_3_DAYS"
    elif days_until_due <= 7:
        return "DUE_4_7_DAYS"
    else:
        return "DUE_LATER"


def analyze_payment_due(
    invoice_id: str,
    supplier_name: str,
    amount: float,
    invoice_date: datetime,
    payment_terms: str | None,
    today: datetime | None = None,
) -> PaymentDueInfo:
    """Analyze a single invoice's payment due status."""
    if today is None:
        today = datetime.now(timezone.utc)

    terms_days = parse_payment_terms_days(payment_terms)
    due_date = invoice_date + timedelta(days=terms_days)
    days_until_due = (due_date.date() - today.date()).days if hasattr(due_date, 'date') else (due_date - today).days
    category = categorize_payment(days_until_due)

    return PaymentDueInfo(
        invoice_id=invoice_id,
        supplier_name=supplier_name,
        amount=amount,
        invoice_date=invoice_date.strftime("%Y-%m-%d") if hasattr(invoice_date, 'strftime') else str(invoice_date),
        payment_terms_days=terms_days,
        due_date=due_date.strftime("%Y-%m-%d") if hasattr(due_date, 'strftime') else str(due_date),
        days_until_due=days_until_due,
        category=category,
        is_overdue=days_until_due < 0,
    )
