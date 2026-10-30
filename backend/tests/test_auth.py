def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@edtech.org", "password": "AdminSecurePassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful."
    assert data["admin"]["email"] == "admin@edtech.org"
    # Ensure HttpOnly cookie is returned
    assert "edtech_token" in response.cookies


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@edtech.org", "password": "WrongPassword123"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_email(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@edtech.org", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_current_admin_me_success(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "admin@edtech.org"


def test_get_current_admin_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_logout(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."
