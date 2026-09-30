import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.security.dependencies import requires_role
from app.security.roles import UserRole, has_role


def test_role_hierarchy_checks():
    # Customer only satisfies Customer
    assert has_role("CUSTOMER", [UserRole.CUSTOMER]) is True
    assert has_role("CUSTOMER", [UserRole.SUPPORT_AGENT]) is False
    assert has_role("CUSTOMER", [UserRole.SUPERVISOR]) is False
    assert has_role("CUSTOMER", [UserRole.ADMIN]) is False

    # Support Agent satisfies Customer and Support Agent
    assert has_role("SUPPORT_AGENT", [UserRole.CUSTOMER]) is True
    assert has_role("SUPPORT_AGENT", [UserRole.SUPPORT_AGENT]) is True
    assert has_role("SUPPORT_AGENT", [UserRole.SUPERVISOR]) is False

    # Supervisor satisfies Customer, Support Agent, and Supervisor
    assert has_role("SUPERVISOR", [UserRole.CUSTOMER]) is True
    assert has_role("SUPERVISOR", [UserRole.SUPPORT_AGENT]) is True
    assert has_role("SUPERVISOR", [UserRole.SUPERVISOR]) is True
    assert has_role("SUPERVISOR", [UserRole.ADMIN]) is False

    # Admin satisfies everything
    assert has_role("ADMIN", [UserRole.CUSTOMER]) is True
    assert has_role("ADMIN", [UserRole.SUPPORT_AGENT]) is True
    assert has_role("ADMIN", [UserRole.SUPERVISOR]) is True
    assert has_role("ADMIN", [UserRole.ADMIN]) is True


def test_requires_role_dependency_behavior():
    app = FastAPI()

    # Mock user dependency
    test_user = {"user_id": "test_uid", "role": "CUSTOMER"}

    def get_test_user():
        return test_user

    @app.get("/customer-only", dependencies=[Depends(requires_role([UserRole.CUSTOMER]))])
    def customer_route():
        return {"status": "ok"}

    @app.get("/supervisor-only", dependencies=[Depends(requires_role([UserRole.SUPERVISOR]))])
    def supervisor_route():
        return {"status": "ok"}

    from app.security.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = get_test_user
    client = TestClient(app)

    # 1. Customer user accesses customer route -> 200
    res1 = client.get("/customer-only")
    assert res1.status_code == 200

    # 2. Customer user accesses supervisor route -> 403 Forbidden
    res2 = client.get("/supervisor-only")
    assert res2.status_code == 403

    # 3. Change role to SUPERVISOR -> 200
    test_user["role"] = "SUPERVISOR"
    res3 = client.get("/supervisor-only")
    assert res3.status_code == 200
