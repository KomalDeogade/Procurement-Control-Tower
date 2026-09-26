"""
Approval rules – deterministic, code-based rules for procurement approvals.

These rules are the source of truth.  AI may recommend, but these rules decide.
"""

from dataclasses import dataclass


@dataclass
class ApprovalRule:
    """Defines thresholds for automatic vs. manual approval."""

    # PO values below this threshold may be auto-approved
    auto_approve_threshold: float = 5_000.00

    # PO values above this require manager approval
    manager_approval_threshold: float = 5_000.00

    # PO values above this require finance approval
    finance_approval_threshold: float = 50_000.00

    # Maximum allowed variance between quote and invoice (percentage)
    invoice_variance_tolerance: float = 5.0


# Singleton rule set (can be made configurable later)
APPROVAL_RULES = ApprovalRule()


def determine_approval_level(total_amount: float) -> list[str]:
    """
    Return the list of roles required to approve a purchase order.

    Business logic is deterministic – not AI-generated.
    """
    levels: list[str] = []

    if total_amount <= APPROVAL_RULES.auto_approve_threshold:
        return []  # Auto-approved

    if total_amount > APPROVAL_RULES.manager_approval_threshold:
        levels.append("PROCUREMENT_MANAGER")

    if total_amount > APPROVAL_RULES.finance_approval_threshold:
        levels.append("FINANCE_USER")

    return levels


def validate_invoice_against_po(
    po_amount: float,
    invoice_amount: float,
) -> tuple[bool, str]:
    """
    3-way matching: compare invoice amount against PO amount.

    Returns (is_valid, message).
    """
    if po_amount == 0:
        return False, "PO amount is zero – cannot validate."

    variance = abs(invoice_amount - po_amount) / po_amount * 100

    if variance <= APPROVAL_RULES.invoice_variance_tolerance:
        return True, f"Invoice within tolerance ({variance:.1f}%)."

    return False, (
        f"Invoice variance {variance:.1f}% exceeds tolerance "
        f"of {APPROVAL_RULES.invoice_variance_tolerance}%."
    )


def is_payment_overdue(due_date_str: str, current_date_str: str) -> bool:
    """Deterministic overdue check based on dates."""
    from datetime import datetime

    due = datetime.fromisoformat(due_date_str)
    now = datetime.fromisoformat(current_date_str)
    return now > due
