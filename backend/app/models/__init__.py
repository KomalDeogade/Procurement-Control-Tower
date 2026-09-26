"""
Domain models package.

Import every model here so that Alembic and SQLAlchemy can discover them
when ``from app.models import *`` is used in alembic/env.py.
"""

from app.models.user import User, UserRole                              # noqa: F401
from app.models.requirement import Requirement, RequirementStatus       # noqa: F401
from app.models.supplier import Supplier                                # noqa: F401
from app.models.rfq import RFQ, RFQStatus                              # noqa: F401
from app.models.supplier_quote import SupplierQuote                     # noqa: F401
from app.models.approval import Approval, ApprovalStatus                # noqa: F401
from app.models.purchase_order import PurchaseOrder                     # noqa: F401
from app.models.goods_receipt import GoodsReceipt                       # noqa: F401
from app.models.inventory import InventoryItem, InventoryTransaction    # noqa: F401
from app.models.invoice import Invoice                                  # noqa: F401
from app.models.payment import Payment                                  # noqa: F401
from app.models.notification import Notification                        # noqa: F401
from app.models.audit_log import AuditLog                               # noqa: F401
