"""
SAP Adapter – abstraction layer for SAP communication.

The application NEVER calls SAP directly.  All interaction flows through:

    Frontend → FastAPI → SAPAdapter → Mock SAP (or Real SAP in future)

``SAPAdapter`` is the abstract interface.
``MockSAPAdapter`` implements it by calling the Mock SAP FastAPI service.

To switch to a real SAP system later, create ``RealSAPAdapter`` implementing
the same interface and swap the factory function.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.core.config import settings


# ── Abstract Interface ───────────────────────────────────────
class SAPAdapter(ABC):
    """Interface that all SAP adapters must implement."""

    @abstractmethod
    async def get_suppliers(self) -> list[dict]:
        ...

    @abstractmethod
    async def get_materials(self) -> list[dict]:
        ...

    @abstractmethod
    async def get_inventory(self) -> list[dict]:
        ...

    @abstractmethod
    async def create_purchase_requisition(self, data: dict) -> dict:
        ...

    @abstractmethod
    async def create_purchase_order(self, data: dict) -> dict:
        ...

    @abstractmethod
    async def get_purchase_order(self, po_id: str) -> dict:
        ...

    @abstractmethod
    async def create_goods_receipt(self, data: dict) -> dict:
        ...

    @abstractmethod
    async def create_invoice(self, data: dict) -> dict:
        ...

    @abstractmethod
    async def get_invoice(self, invoice_id: str) -> dict:
        ...

    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> dict:
        ...


# ── Mock SAP Adapter (calls the Mock SAP FastAPI service) ────
class MockSAPAdapter(SAPAdapter):
    """Communicates with the Mock SAP FastAPI service over HTTP."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.MOCK_SAP_URL).rstrip("/")

    async def _request(
        self, method: str, path: str, json: dict | None = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, f"{self.base_url}{path}", json=json
            )
            response.raise_for_status()
            return response.json()

    async def get_suppliers(self) -> list[dict]:
        return await self._request("GET", "/sap/suppliers")

    async def get_materials(self) -> list[dict]:
        return await self._request("GET", "/sap/materials")

    async def get_inventory(self) -> list[dict]:
        return await self._request("GET", "/sap/inventory")

    async def create_purchase_requisition(self, data: dict) -> dict:
        return await self._request("POST", "/sap/purchase-requisitions", json=data)

    async def create_purchase_order(self, data: dict) -> dict:
        return await self._request("POST", "/sap/purchase-orders", json=data)

    async def get_purchase_order(self, po_id: str) -> dict:
        return await self._request("GET", f"/sap/purchase-orders/{po_id}")

    async def create_goods_receipt(self, data: dict) -> dict:
        return await self._request("POST", "/sap/goods-receipts", json=data)

    async def create_invoice(self, data: dict) -> dict:
        return await self._request("POST", "/sap/invoices", json=data)

    async def get_invoice(self, invoice_id: str) -> dict:
        return await self._request("GET", f"/sap/invoices/{invoice_id}")

    async def get_payment_status(self, payment_id: str) -> dict:
        return await self._request("GET", f"/sap/payment-status/{payment_id}")


# ── Factory ──────────────────────────────────────────────────
def get_sap_adapter() -> SAPAdapter:
    """Factory function – swap implementation here when moving to real SAP."""
    return MockSAPAdapter()
