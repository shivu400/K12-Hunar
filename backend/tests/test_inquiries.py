def test_submit_valid_inquiry(client):
    payload = {
        "user_type": "Parent",
        "category": "Scholarship",
        "name": "Maria Garcia",
        "email": "maria@example.com",
        "phone": "+1 (555) 234-5678",
        "message": "I would like to inquire about merit scholarship criteria.",
    }
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Maria Garcia"
    assert data["status"] == "New"
    assert data["category"] == "Scholarship"
    assert data["user_type"] == "Parent"


def test_submit_invalid_inquiry_rejected(client):
    # Invalid user_type, short name, bad phone, short message
    payload = {
        "user_type": "InvalidType",
        "category": "Scholarship",
        "name": "A",
        "email": "not-an-email",
        "phone": "12",
        "message": "Too short",
    }
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data


def test_protected_dashboard_unauthorized_without_cookie(client):
    response = client.get("/api/inquiries")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_list_inquiries_authenticated(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 2
    assert data["page"] == 1


def test_category_filtering(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries?category=Scholarship")
    assert response.status_code == 200
    data = response.json()
    assert all(item["category"] == "Scholarship" for item in data["items"])


def test_user_type_filtering(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries?userType=Student")
    assert response.status_code == 200
    data = response.json()
    assert all(item["user_type"] == "Student" for item in data["items"])


def test_search_by_name(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries?search=Jane")
    assert response.status_code == 200
    data = response.json()
    assert any("Jane" in item["name"] for item in data["items"])


def test_search_by_phone(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries?search=98765")
    assert response.status_code == 200
    data = response.json()
    assert any("98765" in item["phone"] for item in data["items"])


def test_combined_filters(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.get("/api/inquiries?category=Scholarship&userType=Parent&search=Jane")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Jane Doe"


def test_valid_status_update(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.patch(
        "/api/inquiries/inq-1/status",
        json={"status": "Resolved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Resolved"


def test_invalid_status_update_rejected(client, admin_auth_cookie):
    client.cookies.update(admin_auth_cookie)
    response = client.patch(
        "/api/inquiries/inq-1/status",
        json={"status": "Archived"},  # Not in ('New', 'In Progress', 'Resolved')
    )
    assert response.status_code == 422
