import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.main import app
from app.database import get_db_connection
from app.security import hash_password, create_access_token


class MockCursor:
    def __init__(self, db_state):
        self.db = db_state
        self._last_result = None
        self._last_results = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params=None):
        query_str = " ".join(query.strip().split())
        params = list(params) if params else []

        # 1. Admin queries
        if "FROM admins WHERE LOWER(email) = LOWER(%s)" in query_str:
            email_target = params[0].strip().lower()
            found = next((a for a in self.db["admins"] if a["email"].lower() == email_target), None)
            self._last_result = dict(found) if found else None

        elif "FROM admins WHERE id = %s" in query_str:
            admin_id = str(params[0])
            found = next((a for a in self.db["admins"] if str(a["id"]) == admin_id), None)
            self._last_result = dict(found) if found else None

        # 2. Inquiry Insert
        elif "INSERT INTO inquiries" in query_str:
            # (user_type, category, name, email, phone, message)
            new_id = f"mock-uuid-{len(self.db['inquiries']) + 1}"
            now_iso = "2026-10-29T12:00:00Z"
            record = {
                "id": new_id,
                "user_type": params[0],
                "category": params[1],
                "name": params[2],
                "email": params[3],
                "phone": params[4],
                "message": params[5],
                "status": "New",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            self.db["inquiries"].append(record)
            self._last_result = dict(record)

        # 3. Inquiry Count
        elif "SELECT COUNT(*) AS total FROM inquiries" in query_str:
            filtered = self._apply_filters(params)
            self._last_result = {"total": len(filtered)}

        # 4. Inquiry Select List
        elif "SELECT id, user_type, category, name, email, phone, message, status, created_at, updated_at FROM inquiries" in query_str and "ORDER BY" in query_str:
            # Query params has filter params followed by [limit, offset]
            limit = params[-2]
            offset = params[-1]
            filter_params = params[:-2]
            filtered = self._apply_filters(filter_params)
            # stable sort newest first
            sorted_items = sorted(filtered, key=lambda x: (x["created_at"], x["id"]), reverse=True)
            page_slice = sorted_items[offset : offset + limit]
            self._last_results = [dict(item) for item in page_slice]

        # 5. Inquiry Select Single
        elif "FROM inquiries WHERE id = %s" in query_str:
            inquiry_id = str(params[0])
            found = next((i for i in self.db["inquiries"] if str(i["id"]) == inquiry_id), None)
            self._last_result = dict(found) if found else None

        # 6. Inquiry Status Update
        elif "UPDATE inquiries SET status = %s" in query_str:
            new_status = params[0]
            inquiry_id = str(params[1])
            found = next((i for i in self.db["inquiries"] if str(i["id"]) == inquiry_id), None)
            if found:
                found["status"] = new_status
                found["updated_at"] = "2026-10-29T12:30:00Z"
                self._last_result = dict(found)
            else:
                self._last_result = None

    def _apply_filters(self, filter_params):
        results = self.db["inquiries"]
        for p in filter_params:
            if isinstance(p, str) and p.startswith("%") and p.endswith("%"):
                # Search filter
                term = p[1:-1].lower()
                results = [r for r in results if term in r["name"].lower() or term in r["phone"].lower()]
            elif p in ("Scholarship", "Concert", "Admission", "General Query"):
                results = [r for r in results if r["category"] == p]
            elif p in ("Parent", "Student", "School"):
                results = [r for r in results if r["user_type"] == p]
        return results

    def fetchone(self):
        return self._last_result

    def fetchall(self):
        return self._last_results


class MockConnection:
    def __init__(self, db_state):
        self.db = db_state

    def cursor(self):
        return MockCursor(self.db)

    def commit(self):
        pass

    def rollback(self):
        pass


@pytest.fixture
def mock_db_state():
    test_admin_pwd_hash = hash_password("AdminSecurePassword123!")
    return {
        "admins": [
            {
                "id": "11111111-2222-3333-4444-555555555555",
                "email": "admin@edtech.org",
                "password_hash": test_admin_pwd_hash,
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        "inquiries": [
            {
                "id": "inq-1",
                "user_type": "Parent",
                "category": "Scholarship",
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1-555-019-2834",
                "message": "Interested in scholarship eligibility details.",
                "status": "New",
                "created_at": "2026-10-28T10:00:00Z",
                "updated_at": "2026-10-28T10:00:00Z",
            },
            {
                "id": "inq-2",
                "user_type": "Student",
                "category": "Admission",
                "name": "Alex Smith",
                "email": "alex@example.com",
                "phone": "+91 98765 43210",
                "message": "Looking for admission deadline schedule.",
                "status": "In Progress",
                "created_at": "2026-10-29T08:00:00Z",
                "updated_at": "2026-10-29T08:00:00Z",
            },
        ],
    }


@pytest.fixture
def client(mock_db_state):
    mock_conn = MockConnection(mock_db_state)

    def override_get_db():
        yield mock_conn

    app.dependency_overrides[get_db_connection] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_auth_cookie(mock_db_state):
    admin = mock_db_state["admins"][0]
    token = create_access_token(admin["id"], admin["email"])
    return {"edtech_token": token}
