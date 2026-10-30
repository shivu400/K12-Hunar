# EdTech CRM and Inquiry System

A complete, production-grade EdTech Inquiry and CRM web application built for admissions, scholarship, and concert inquiries. Features a public inquiry form with dual-layer validation, custom backend JWT authentication with secure HttpOnly cookies, and a protected administration dashboard with dynamic parameterized filtering, debounced search, server-side pagination, and inquiry status management.

---

## 1. Project Overview & Implemented Requirements

- **Public Inquiry Submission**:
  - Captures `user_type` (`Parent`, `Student`, `School`), `category` (`Scholarship`, `Concert`, `Admission`, `General Query`), `name`, `email`, `phone`, and `message`.
  - Dual-layer validation (client-side immediate UX feedback + server-side Pydantic models).
  - Trims text inputs, validates international phone format, protects against duplicate submissions while in flight, and preserves form values on error.
- **Custom Admin Authentication**:
  - Direct PostgreSQL admin storage (no Supabase Auth or third-party auth services).
  - Secure password hashing and verification using `bcrypt` (enforcing the 72-byte restriction).
  - Stateless JWT issuance via `PyJWT` with explicit HS256 algorithm and expiration.
  - Token delivered exclusively via **HttpOnly, SameSite=Lax** cookies (`Secure=True` in production), preventing XSS token exfiltration.
  - Protected backend routes guarded by FastAPI dependency `require_admin`.
  - Frontend route guard (`ProtectedRoute`) redirecting unauthenticated users to `/admin/login`.
  - Login rate limiter preventing brute-force password guessing.
  - Safe CLI provisioning script for administrators (`python -m scripts.create_admin`).
- **Protected Admin Dashboard**:
  - Tabular view: Date, Name, Phone, Email, User Type, Category, Status, Actions.
  - **Mandatory Filters**: Category, User Type, and Search by Name OR Phone Number.
  - Dynamic parameterized SQL queries with clean multi-condition combination.
  - Debounced search input (350ms) and request-race-condition guards preventing stale responses.
  - Server-side pagination with stable secondary sorting (`created_at DESC, id DESC`).
  - Inquiry status updates (`New`, `In Progress`, `Resolved`) with database-enforced CHECK constraints.
  - Modal drawer to inspect full multiline messages.
- **Database & Architecture**:
  - Supabase PostgreSQL accessed via `psycopg 3` connection pooling (`psycopg_pool.ConnectionPool`).
  - Raw parameterized SQL; no ORM.
  - Row Level Security (RLS) enabled to ensure public PostgREST APIs cannot expose student data.

---

## 2. Tech Stack

- **Frontend**: React 18, Vite, React Router v6, Vanilla CSS (responsive, clean typography).
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings.
- **Database**: Supabase PostgreSQL.
- **Driver**: Psycopg 3 (`psycopg[binary,pool]`) with synchronous connection pooling.
- **Security**: `bcrypt` for password hashing, `PyJWT` for JWT signing and verification.
- **Testing**: `pytest`, `httpx`, and FastAPI `TestClient`.

---

## 3. Project Directory Structure

```text
├── schema.sql                         # PostgreSQL schema with constraints, indexes & RLS
├── README.md                          # Comprehensive project documentation
├── .gitignore                         # Git exclusion rules
├── backend/
│   ├── .env.example                   # Backend environment template
│   ├── requirements.txt               # Production Python dependencies
│   ├── requirements-dev.txt           # Test and development dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, lifespan, SPA fallback
│   │   ├── config.py                  # Pydantic Settings configuration
│   │   ├── database.py                # Psycopg 3 connection pool & session dependency
│   │   ├── security.py                # bcrypt hashing & PyJWT token utilities
│   │   ├── dependencies.py            # require_admin authentication dependency
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # POST /login, POST /logout, GET /me
│   │   │   └── inquiries.py           # POST/GET /inquiries, PATCH /inquiries/:id/status
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # LoginRequest, AdminResponse, etc.
│   │   │   └── inquiries.py           # InquiryCreate, InquiryListResponse, etc.
│   │   └── queries/
│   │       ├── __init__.py
│   │       ├── admins.py              # Parameterized admin SQL operations
│   │       └── inquiries.py           # Parameterized inquiry SQL queries & filters
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── create_admin.py            # Secure CLI script for provisioning admins
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Pytest fixtures & mock connection overrides
│       ├── test_auth.py               # Authentication integration test suite
│       └── test_inquiries.py          # Inquiries and dashboard filter test suite
└── frontend/
    ├── .env.example                   # Frontend environment template
    ├── package.json                   # React & Vite npm dependencies
    ├── vite.config.js                 # Vite dev proxy configuration
    ├── index.html                     # HTML5 entrypoint with Google Fonts
    └── src/
        ├── main.jsx                   # React DOM root & BrowserRouter
        ├── App.jsx                    # Header, Navigation, and Route definitions
        ├── index.css                  # Restrained design system and responsive layout
        ├── api.js                     # Fetch client with credentials & CSRF header
        ├── context/
        │   └── AuthContext.jsx        # Admin session provider
        ├── components/
        │   └── ProtectedRoute.jsx     # Route guard component
        └── pages/
            ├── InquiryPage.jsx        # Public inquiry form
            ├── LoginPage.jsx          # Admin authentication form
            ├── DashboardPage.jsx      # Filterable dashboard & detail modal
            └── NotFoundPage.jsx       # 404 fallback page
```

---

## 4. API Specification & Contracts

### Public Endpoints
- `GET /api/health`
  - Response `200 OK`: `{"status": "healthy", "environment": "...", "database": "connected"}`
- `POST /api/inquiries`
  - Body: `{ "user_type": "Student", "category": "Admission", "name": "...", "email": "...", "phone": "...", "message": "..." }`
  - Response `201 Created`: Full created inquiry object.
  - Response `422 Unprocessable Entity`: Validation error map `{ "detail": "...", "errors": { ... } }`.

### Authentication Endpoints
- `POST /api/auth/login`
  - Body: `{ "email": "admin@edtech.org", "password": "..." }`
  - Sets `edtech_token` HttpOnly cookie.
  - Response `200 OK`: `{ "message": "Login successful.", "admin": { "id": "...", "email": "..." } }`
- `POST /api/auth/logout`
  - Clears `edtech_token` cookie.
  - Response `200 OK`: `{ "message": "Logged out successfully." }`
- `GET /api/auth/me`
  - Protected by `require_admin`.
  - Response `200 OK`: `{ "id": "...", "email": "..." }`

### Protected Dashboard Endpoints
- `GET /api/inquiries?category=...&userType=...&search=...&page=1&limit=10`
  - Protected by `require_admin`.
  - Response `200 OK`: `{ "items": [...], "page": 1, "limit": 10, "total": 12, "total_pages": 2 }`
- `GET /api/inquiries/:id`
  - Protected by `require_admin`.
  - Response `200 OK`: Single inquiry object including multiline message.
- `PATCH /api/inquiries/:id/status`
  - Protected by `require_admin`.
  - Body: `{ "status": "In Progress" }`
  - Response `200 OK`: Updated inquiry record.

---

## 5. Prerequisites

- Python 3.10 or higher.
- Node.js 18+ and npm.
- Supabase account (or local PostgreSQL instance).

---

## 6. Supabase Database Setup

1. Open your [Supabase Dashboard](https://supabase.com/dashboard) and select your project.
2. Navigate to the **SQL Editor** tab on the left sidebar.
3. Open `schema.sql` from the root of this repository, copy its entire contents, paste them into the SQL editor, and click **Run**.
4. Navigate to **Project Settings > Database**:
   - Locate the **Connection string** section.
   - Select **URI**.
   - Copy the connection string. It will look like:
     ```
     postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
     ```
   - Replace `[YOUR-PASSWORD]` with your actual database password.

> **Security Note on Supabase Data APIs:**
> Supabase automatically exposes tables to PostgREST under the `anon` key. In `schema.sql`, Row Level Security (RLS) is enabled on `admins` and `inquiries`, and anonymous access is denied. Our FastAPI backend connects directly via PostgreSQL connection pooler (which uses the PostgreSQL credentials and bypasses client RLS), ensuring inquiry data is never exposed directly through public PostgREST endpoints.

---

## 7. Local Installation & Setup

### A. Backend Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   - **Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Configure environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and set your `DATABASE_URL` and a secret `JWT_SECRET`.
5. Provision the initial Administrator:
   ```bash
   python -m scripts.create_admin
   ```
   Follow the prompts to enter an email and password (or supply them in `.env`). The password will be hashed using bcrypt before insertion.
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will run at `http://localhost:8000`. Interactive documentation is available at `http://localhost:8000/api/docs`.

### B. Frontend Setup

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. (Optional) Configure environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - By default, Vite proxies `/api` calls directly to `http://localhost:8000`, so `VITE_API_BASE_URL` can remain blank in development.
4. Start the frontend development server:
   ```bash
   npm run dev
   ```
5. Open your browser and navigate to `http://localhost:5173`.

---

## 8. Running Automated Tests

A comprehensive integration test suite is provided in `backend/tests/` covering inquiry validation, unauthorized route rejection, admin login, filter combinations, search, and status updates.

To execute the automated tests:
```bash
cd backend
pytest -v
```

All database operations in the test suite are executed using in-memory mocked connection fixtures, guaranteeing no destructive modifications or network dependencies on production databases.

---

## 9. Manual Verification Checklist

Follow this end-to-end verification checklist:

1. **Submit Inquiry**:
   - Go to `http://localhost:5173`.
   - Select `Parent`, `Scholarship`, enter `Jane Doe`, `jane@example.com`, `+1 (555) 019-2834`, and an inquiry message.
   - Click **Submit Inquiry**. Confirm the success notification appears and form fields clear.
2. **Verify Database Record**:
   - Check the `inquiries` table in Supabase Table Editor; verify the newly submitted row exists with status `'New'`.
3. **Verify Route Guard**:
   - Navigate directly to `http://localhost:5173/admin/dashboard`.
   - Verify that the app redirects to `/admin/login`.
4. **Log In as Admin**:
   - Enter the admin credentials created during step 5 of the backend setup.
   - Click **Sign In**. Confirm redirect to `/admin/dashboard`.
5. **Inspect HttpOnly Cookie**:
   - In browser DevTools > Application > Cookies, confirm the `edtech_token` cookie is present with `HttpOnly` enabled.
6. **Apply Filters**:
   - Select Category `Scholarship` and User Type `Parent`. Verify table updates to display only matching items.
7. **Test Search**:
   - In the search input, type `Jane` or `019`. Verify debounce triggers and returns the matching row.
8. **View Message & Update Status**:
   - Click **View Message**. Confirm the modal opens with the full message.
   - Change the status dropdown from `New` to `In Progress`. Confirm the badge updates immediately.
9. **Log Out**:
   - Click **Sign Out**. Confirm you are returned to the login screen and the cookie is cleared.
10. **Verify Backend Rejection**:
    - Attempt a `GET /api/inquiries` request via curl or Postman without cookie headers; confirm a `401 Unauthorized` response is returned.

---

## 10. Production Deployment Strategy

### Recommended Architecture: Single-Origin Deployment
To avoid third-party cookie restrictions in modern browsers (such as Chrome, Safari, and Brave), the recommended deployment strategy is to serve the React frontend and FastAPI backend under the **same origin**.

1. **Build the Frontend**:
   ```bash
   cd frontend
   npm run build
   ```
   This generates the production bundle inside `frontend/dist/`.
2. **Serve from FastAPI**:
   FastAPI’s `app/main.py` is preconfigured to serve the compiled bundle from `frontend/dist/` and handle client-side SPA routing fallbacks for all non-API paths.
3. **Run with Uvicorn**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. **Environment Variables**:
   - Set `ENVIRONMENT=production` to ensure cookies have `Secure=True`.
   - Set `DATABASE_URL` to your Supabase PostgreSQL pooler URI with `sslmode=require`.

### Alternative: Separate Hosting (e.g., Vercel + Render)
If frontend and backend are hosted on separate domains (e.g., `https://frontend.vercel.app` and `https://backend.onrender.com`):
- `FRONTEND_ORIGIN` in backend `.env` must match the frontend URL.
- Cookies must specify `SameSite=None` and `Secure=True`.
- Note: Third-party cookie blocking may affect users with strict browser privacy settings unless a custom domain with shared apex is used (e.g., `app.domain.com` and `api.domain.com`).

---

## 11. Important Security & Design Decisions

- **Why bcrypt over Argon2 for this project?**
  - Strictly chosen to adhere to assessment specifications. Password length is capped at 72 bytes defensively to prevent bcrypt's native truncation vulnerability.
- **Why HttpOnly Cookies over LocalStorage?**
  - Storing JWTs in `localStorage` leaves tokens vulnerable to exfiltration via Cross-Site Scripting (XSS). HttpOnly cookies cannot be accessed by client JavaScript.
- **CSRF Protection Strategy**:
  - The API combines `SameSite=Lax` cookies with custom request headers (`X-Requested-With: XMLHttpRequest`). Cross-origin form submissions cannot forge custom headers, mitigating CSRF risks.
- **Stateless Logout Semantics**:
  - `POST /api/auth/logout` clears the browser cookie. In a stateless JWT architecture, the client cookie is discarded; for immediate revocation before token expiry across distributed systems, short TTLs (or a Redis-backed token denylist) can be introduced.
- **Parameterized SQL**:
  - All database queries, filter clauses, and search terms use `psycopg` `%s` positional placeholders, eliminating SQL injection vulnerabilities.

---

## 12. Assessment Submission Details

- **GitHub Repository**: `[PASTE_REPOSITORY_URL_HERE]`
- **Live Demo**: `[PASTE_LIVE_DEMO_URL_HERE]`
