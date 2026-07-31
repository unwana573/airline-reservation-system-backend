import jwt
import pytest

pytestmark = pytest.mark.asyncio

VALID_REGISTER_PAYLOAD = {
    "title": "Mr",
    "first_name": "Test",
    "last_name": "Pilot",
    "email": "pilot@example.com",
    "password": "flyhigh123",
    "confirm_password": "flyhigh123",
    "accept_terms": True,
    "marketing_opt_in": False,
}


async def test_register_new_user(client):
    response = await client.post("/api/v1/auth/register", json=VALID_REGISTER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "pilot@example.com"
    assert body["first_name"] == "Test"
    assert body["last_name"] == "Pilot"
    assert body["role"] == "customer"
    assert "password" not in body


async def test_register_rejects_mismatched_passwords(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "mismatch@example.com", "confirm_password": "different123"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_rejects_unaccepted_terms(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "noterms@example.com", "accept_terms": False}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_duplicate_email_rejected(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "duplicate@example.com"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


async def test_login_success_returns_token_pair(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "login@example.com"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "flyhigh123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_rejected(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "wrongpass@example.com"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post(
        "/api/v1/auth/login", json={"email": "wrongpass@example.com", "password": "nope12345"}
    )
    assert response.status_code == 401


async def test_remember_me_extends_refresh_token_lifetime(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "remember@example.com"}
    await client.post("/api/v1/auth/register", json=payload)

    short_session = await client.post(
        "/api/v1/auth/login",
        json={"email": "remember@example.com", "password": "flyhigh123", "remember_me": False},
    )
    long_session = await client.post(
        "/api/v1/auth/login",
        json={"email": "remember@example.com", "password": "flyhigh123", "remember_me": True},
    )

    short_token = short_session.json()["refresh_token"]
    long_token = long_session.json()["refresh_token"]

    short_exp = jwt.decode(short_token, options={"verify_signature": False})["exp"]
    long_exp = jwt.decode(long_token, options={"verify_signature": False})["exp"]

    assert long_exp > short_exp


async def test_me_requires_valid_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_with_valid_token_returns_profile(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "me@example.com"}
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post("/api/v1/auth/login", json={"email": "me@example.com", "password": "flyhigh123"})
    token = login.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_refresh_token_issues_new_pair(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "refresh@example.com"}
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post(
        "/api/v1/auth/login", json={"email": "refresh@example.com", "password": "flyhigh123"}
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_password_reset_flow(client):
    payload = {**VALID_REGISTER_PAYLOAD, "email": "reset@example.com", "password": "oldpassword1", "confirm_password": "oldpassword1"}
    await client.post("/api/v1/auth/register", json=payload)

    forgot = await client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    reset_token = forgot.json()["dev_reset_token"]

    reset = await client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "newpassword2"}
    )
    assert reset.status_code == 200

    old_login = await client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": "oldpassword1"}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": "newpassword2"}
    )
    assert new_login.status_code == 200


async def test_forgot_password_unknown_email_does_not_leak(client):
    response = await client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"})
    assert response.status_code == 200
    assert "dev_reset_token" not in response.json()


async def test_google_oauth_without_server_config_returns_503(client):
    # No GOOGLE_CLIENT_ID configured in this test environment — server should
    # fail clearly rather than silently accepting unverifiable tokens.
    response = await client.post("/api/v1/auth/oauth/google", json={"id_token": "fake-token"})
    assert response.status_code == 503