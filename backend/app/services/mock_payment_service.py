"""
Mock Payment Service – simulates bank payment processing.

This is NOT a real bank integration.
"""

import random
import string
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class MockPaymentResult:
    payment_id: str
    amount: float
    supplier_name: str
    status: str  # SUCCESS, FAILED, PROCESSING
    transaction_reference: str
    processed_at: str
    is_simulation: bool = True

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "amount": self.amount,
            "supplier_name": self.supplier_name,
            "status": self.status,
            "transaction_reference": self.transaction_reference,
            "processed_at": self.processed_at,
            "is_simulation": self.is_simulation,
            "disclaimer": "⚠ This is a SIMULATED payment – no real funds transferred.",
        }


def process_mock_payment(
    payment_id: str,
    amount: float,
    supplier_name: str,
    simulate_failure: bool = False,
) -> MockPaymentResult:
    """
    Simulate payment processing.

    95% success rate unless simulate_failure=True.
    """
    ref_suffix = "".join(random.choices(string.digits, k=5))
    txn_ref = f"MOCK-TXN-{ref_suffix}"
    now = datetime.now(timezone.utc).isoformat()

    if simulate_failure:
        status = "FAILED"
    elif random.random() < 0.95:
        status = "SUCCESS"
    else:
        status = "FAILED"

    return MockPaymentResult(
        payment_id=payment_id,
        amount=amount,
        supplier_name=supplier_name,
        status=status,
        transaction_reference=txn_ref,
        processed_at=now,
    )
