"""
Three-way matching service – PO + GRN + Invoice.

Deterministic comparison – no AI.
Tolerance: configurable (default 5%).
"""

from dataclasses import dataclass


@dataclass
class MatchResult:
    status: str  # MATCHED, MISMATCH
    quantity_match: bool
    price_match: bool
    amount_match: bool
    po_quantity: float
    grn_quantity: float
    invoice_quantity: float
    po_unit_price: float
    invoice_unit_price: float
    po_total: float
    invoice_total: float
    quantity_variance_pct: float
    price_variance_pct: float
    amount_variance_pct: float
    exceptions: list[str]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "quantity_match": self.quantity_match,
            "price_match": self.price_match,
            "amount_match": self.amount_match,
            "po_quantity": self.po_quantity,
            "grn_quantity": self.grn_quantity,
            "invoice_quantity": self.invoice_quantity,
            "po_unit_price": self.po_unit_price,
            "invoice_unit_price": self.invoice_unit_price,
            "po_total": self.po_total,
            "invoice_total": self.invoice_total,
            "quantity_variance_pct": self.quantity_variance_pct,
            "price_variance_pct": self.price_variance_pct,
            "amount_variance_pct": self.amount_variance_pct,
            "exceptions": self.exceptions,
        }


def _variance_pct(expected: float, actual: float) -> float:
    """Calculate % variance. Positive = over, negative = under."""
    if expected == 0:
        return 100.0 if actual != 0 else 0.0
    return round(((actual - expected) / expected) * 100, 2)


def three_way_match(
    po_quantity: float,
    po_unit_price: float,
    po_total: float,
    grn_quantity: float,
    invoice_quantity: float,
    invoice_unit_price: float,
    invoice_total: float,
    tolerance_pct: float = 5.0,
) -> MatchResult:
    """
    Compare PO, GRN, and Invoice values.

    Returns MATCHED if all variances are within tolerance.
    Returns MISMATCH with detailed exceptions otherwise.
    """
    exceptions: list[str] = []

    # Quantity check (GRN vs PO, Invoice vs PO)
    qty_var_grn = _variance_pct(po_quantity, grn_quantity)
    qty_var_inv = _variance_pct(po_quantity, invoice_quantity)
    quantity_match = abs(qty_var_grn) <= tolerance_pct and abs(qty_var_inv) <= tolerance_pct

    if abs(qty_var_grn) > tolerance_pct:
        exceptions.append(
            f"GRN quantity ({grn_quantity}) differs from PO ({po_quantity}) by {qty_var_grn}%"
        )
    if abs(qty_var_inv) > tolerance_pct:
        exceptions.append(
            f"Invoice quantity ({invoice_quantity}) differs from PO ({po_quantity}) by {qty_var_inv}%"
        )

    # Price check
    price_var = _variance_pct(po_unit_price, invoice_unit_price)
    price_match = abs(price_var) <= tolerance_pct

    if not price_match:
        exceptions.append(
            f"Invoice unit price ({invoice_unit_price}) differs from PO ({po_unit_price}) by {price_var}%"
        )

    # Total amount check
    amount_var = _variance_pct(po_total, invoice_total)
    amount_match = abs(amount_var) <= tolerance_pct

    if not amount_match:
        exceptions.append(
            f"Invoice total ({invoice_total}) differs from PO ({po_total}) by {amount_var}%"
        )

    overall_status = "MATCHED" if (quantity_match and price_match and amount_match) else "MISMATCH"

    return MatchResult(
        status=overall_status,
        quantity_match=quantity_match,
        price_match=price_match,
        amount_match=amount_match,
        po_quantity=po_quantity,
        grn_quantity=grn_quantity,
        invoice_quantity=invoice_quantity,
        po_unit_price=po_unit_price,
        invoice_unit_price=invoice_unit_price,
        po_total=po_total,
        invoice_total=invoice_total,
        quantity_variance_pct=max(abs(qty_var_grn), abs(qty_var_inv)),
        price_variance_pct=abs(price_var),
        amount_variance_pct=abs(amount_var),
        exceptions=exceptions,
    )
