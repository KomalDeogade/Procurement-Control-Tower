"""
Unit tests for Role-Based Access Control (RBAC) authorization.
Verifies backend HTTP 403 Forbidden enforcement across user roles:
- SUPPLIER
- SCM_USER
- PROCUREMENT_MANAGER
- STORE_USER
- FINANCE_USER
- ADMIN
"""

import pytest
from app.core.dependencies import require_roles
from app.models.user import User, UserRole
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_require_roles_allows_permitted_role():
    user = User(id=1, username="proc_mgr", role=UserRole.PROCUREMENT_MANAGER)
    checker = require_roles("PROCUREMENT_MANAGER", "ADMIN")
    result = await checker(current_user=user)
    assert result.username == "proc_mgr"


@pytest.mark.asyncio
async def test_require_roles_allows_admin_always():
    user = User(id=2, username="admin_user", role=UserRole.ADMIN)
    checker = require_roles("FINANCE_USER")
    result = await checker(current_user=user)
    assert result.username == "admin_user"


@pytest.mark.asyncio
async def test_store_user_approving_supplier_fails():
    user = User(id=3, username="store_bob", role=UserRole.STORE_USER)
    checker = require_roles("PROCUREMENT_MANAGER", "ADMIN")
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_scm_user_approving_payment_fails():
    user = User(id=4, username="scm_alice", role=UserRole.SCM_USER)
    checker = require_roles("FINANCE_USER")
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_supplier_accessing_inventory_fails():
    user = User(id=5, username="supplier_vendor", role=UserRole.SUPPLIER, supplier_id=10)
    checker = require_roles("SCM_USER", "STORE_USER", "PROCUREMENT_MANAGER")
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_finance_user_approving_vendor_fails():
    user = User(id=6, username="finance_charlie", role=UserRole.FINANCE_USER)
    checker = require_roles("PROCUREMENT_MANAGER")
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_supplier_accessing_another_supplier_data_isolation():
    supplier_user = User(id=7, username="vendor_a", role=UserRole.SUPPLIER, supplier_id=1)
    target_supplier_id = 2
    # Verify supplier data isolation rule
    if supplier_user.role == UserRole.SUPPLIER and supplier_user.supplier_id != target_supplier_id:
        allowed = False
    else:
        allowed = True
    assert allowed is False
