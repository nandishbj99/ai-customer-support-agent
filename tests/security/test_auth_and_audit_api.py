import httpx
import pytest
from app.core.database import get_db_session
from app.main import app
from app.seeds.seed_data import det_uuid
from app.security.tokens import token_manager


@pytest.mark.asyncio
async def test_auth_login_refresh_and_logout_flow(db_session):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Customer Login with seed user email
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "aarav.sharma@example.in"},
            )
            assert login_resp.status_code == 200
            data = login_resp.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == "aarav.sharma@example.in"
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]

            # 2. Access /me endpoint with Bearer token
            me_resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert me_resp.status_code == 200
            assert me_resp.json()["user_id"] == data["user"]["id"]
            assert me_resp.json()["role"] == "CUSTOMER"

            # 3. Refresh access token
            ref_resp = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert ref_resp.status_code == 200
            assert "access_token" in ref_resp.json()

            # 4. Logout and revoke tokens
            logout_resp = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_token},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert logout_resp.status_code == 200
            assert logout_resp.json()["status"] == "success"

            # 5. Accessing with revoked token now returns 401
            me_revoked = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert me_revoked.status_code == 401

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_audit_logs_rbac_protection(db_session):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Customer token
            customer_token = token_manager.create_access_token(
                user_id="cust_1", role="CUSTOMER"
            )

            # 2. Supervisor token
            supervisor_token = token_manager.create_access_token(
                user_id="sup_1", role="SUPERVISOR"
            )

            # Customer attempts to read audit logs -> 403 Forbidden
            cust_res = await client.get(
                "/api/v1/audit/logs",
                headers={"Authorization": f"Bearer {customer_token}"},
            )
            assert cust_res.status_code == 403

            # Supervisor reads audit logs -> 200 OK
            sup_res = await client.get(
                "/api/v1/audit/logs",
                headers={"Authorization": f"Bearer {supervisor_token}"},
            )
            assert sup_res.status_code == 200
            assert isinstance(sup_res.json(), list)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_agent_sso_login_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/agent-login",
            json={"email": "agent.smith@bankops.internal", "role": "SUPERVISOR"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["role"] == "SUPERVISOR"
        assert "access_token" in data
