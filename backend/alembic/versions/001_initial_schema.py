"""Initial schema - all domain entities

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("SCM_USER", "PROCUREMENT_MANAGER", "FINANCE_USER", "ADMIN", name="userrole"), nullable=False, server_default="SCM_USER"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Requirements ─────────────────────────────────────
    op.create_table(
        "requirements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("material_code", sa.String(50), nullable=False),
        sa.Column("material_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("plant", sa.String(50)),
        sa.Column("required_by_date", sa.DateTime()),
        sa.Column("budget", sa.Float()),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("priority", sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="requirementpriority"), server_default="MEDIUM"),
        sa.Column("status", sa.Enum("DRAFT", "SUBMITTED", "RFQ_IN_PROGRESS", "QUOTES_RECEIVED", "UNDER_REVIEW", "APPROVAL_PENDING", "APPROVED", "REJECTED", "PO_CREATED", "COMPLETED", "CANCELLED", name="requirementstatus"), server_default="DRAFT"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Suppliers ────────────────────────────────────────
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("supplier_code", sa.String(20), unique=True, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_person", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("designation", sa.String(100)),
        sa.Column("registration_number", sa.String(100)),
        sa.Column("category", sa.String(100)),
        sa.Column("location", sa.String(255)),
        sa.Column("quality_score", sa.Float(), server_default="0.0"),
        sa.Column("delivery_score", sa.Float(), server_default="0.0"),
        sa.Column("historical_performance", sa.Text()),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("payment_terms", sa.String(100)),
        sa.Column("approval_status", sa.String(20), server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Supplier Quotes ──────────────────────────────────
    op.create_table(
        "supplier_quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("requirement_id", sa.Integer(), sa.ForeignKey("requirements.id"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("tax", sa.Float(), server_default="0.0"),
        sa.Column("freight", sa.Float(), server_default="0.0"),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("availability", sa.String(50)),
        sa.Column("lead_time_days", sa.Integer()),
        sa.Column("delivery_date", sa.DateTime()),
        sa.Column("payment_terms", sa.String(100)),
        sa.Column("warranty", sa.String(255)),
        sa.Column("service_details", sa.Text()),
        sa.Column("advantages", sa.Text()),
        sa.Column("limitations", sa.Text()),
        sa.Column("quotation_document", sa.String(500)),
        sa.Column("status", sa.Enum("DRAFT", "SUBMITTED", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "EXPIRED", name="quotestatus"), server_default="DRAFT"),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Approvals ────────────────────────────────────────
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approval_level", sa.Integer(), server_default="1"),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", "REVISION_REQUIRED", name="approvalstatus"), server_default="PENDING"),
        sa.Column("comments", sa.Text()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Purchase Orders ──────────────────────────────────
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("requirement_id", sa.Integer(), sa.ForeignKey("requirements.id"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("supplier_quotes.id")),
        sa.Column("sap_po_number", sa.String(50)),
        sa.Column("material_code", sa.String(50), nullable=False),
        sa.Column("material_name", sa.String(255)),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("delivery_date", sa.DateTime()),
        sa.Column("status", sa.Enum("DRAFT", "PENDING_SAP", "SAP_CREATED", "PARTIALLY_RECEIVED", "FULLY_RECEIVED", "INVOICED", "COMPLETED", "CANCELLED", name="postatus"), server_default="DRAFT"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Goods Receipts ───────────────────────────────────
    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("po_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("received_quantity", sa.Float(), nullable=False),
        sa.Column("received_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("quality_status", sa.Enum("PENDING_INSPECTION", "PASSED", "FAILED", "PARTIAL", name="grnstatus"), server_default="PENDING_INSPECTION"),
        sa.Column("inspector", sa.String(255)),
        sa.Column("remarks", sa.Text()),
        sa.Column("sap_grn_number", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Inventory Items ──────────────────────────────────
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("material_code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("material_name", sa.String(255), nullable=False),
        sa.Column("quantity_on_hand", sa.Float(), server_default="0.0"),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("plant", sa.String(50)),
        sa.Column("warehouse", sa.String(50)),
        sa.Column("reorder_level", sa.Float(), server_default="0.0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Inventory Transactions ───────────────────────────
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("transaction_type", sa.Enum("RECEIPT", "ISSUE", "ADJUSTMENT", "RETURN", "TRANSFER", name="transactiontype"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reference_type", sa.String(50)),
        sa.Column("reference_id", sa.Integer()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )

    # ── Invoices ─────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("po_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("invoice_amount", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), server_default="0.0"),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("invoice_date", sa.DateTime()),
        sa.Column("due_date", sa.DateTime()),
        sa.Column("status", sa.Enum("DRAFT", "SUBMITTED", "VALIDATED", "DISCREPANCY", "APPROVAL_PENDING", "APPROVED", "REJECTED", "PAID", "CANCELLED", name="invoicestatus"), server_default="DRAFT"),
        sa.Column("sap_invoice_number", sa.String(50)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Payments ─────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("display_id", sa.String(20), unique=True, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True)),
        sa.Column("payment_method", sa.Enum("BANK_TRANSFER", "CHECK", "WIRE", name="paymentmethod"), server_default="BANK_TRANSFER"),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED", name="paymentstatus"), server_default="PENDING"),
        sa.Column("reference_number", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Notifications ────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("type", sa.String(50)),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Audit Logs ───────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("old_value", postgresql.JSONB()),
        sa.Column("new_value", postgresql.JSONB()),
        sa.Column("metadata", postgresql.JSONB()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("inventory_transactions")
    op.drop_table("inventory_items")
    op.drop_table("goods_receipts")
    op.drop_table("purchase_orders")
    op.drop_table("approvals")
    op.drop_table("supplier_quotes")
    op.drop_table("suppliers")
    op.drop_table("requirements")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "userrole", "requirementpriority", "requirementstatus", "quotestatus",
        "approvalstatus", "postatus", "grnstatus", "transactiontype",
        "invoicestatus", "paymentmethod", "paymentstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
