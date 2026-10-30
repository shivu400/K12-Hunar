import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
# pyrefly: ignore[missing-import]
from psycopg import Connection
from app.config import get_settings
from app.database import get_db_connection
from app.dependencies import AUTH_COOKIE_NAME, require_admin
from app.queries.admins import get_admin_by_email
from app.schemas.auth import AdminResponse, LoginRequest, LoginResponse, LogoutResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory IP rate limiter for login attempts (5 attempts per minute per IP)
# In high-availability multi-instance setups, Redis or an API gateway can be used.
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60


def check_rate_limit(client_ip: str) -> None:
    now = time.time()
    attempts = _login_attempts[client_ip]
    # Prune timestamps older than window
    valid_attempts = [ts for ts in attempts if now - ts < LOGIN_WINDOW_SECONDS]
    _login_attempts[client_ip] = valid_attempts

    if len(valid_attempts) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute before trying again.",
        )
    _login_attempts[client_ip].append(now)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    conn: Connection = Depends(get_db_connection),
):
    """
    Authenticates an admin using email and password.
    Returns generic 401 on bad credentials to prevent email enumeration.
    Sets secure HttpOnly cookie containing signed JWT.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    admin = get_admin_by_email(conn, payload.email)
    if not admin or not verify_password(payload.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Issue minimal stateless JWT
    token = create_access_token(admin_id=admin["id"], email=admin["email"])
    settings = get_settings()

    # Set secure HttpOnly cookie
    # SameSite='lax' allows smooth same-site and top-level navigation while defending against CSRF
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return LoginResponse(
        message="Login successful.",
        admin=AdminResponse(id=admin["id"], email=admin["email"]),
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response):
    """
    Clears the HttpOnly authentication cookie with matching path and options.
    Note: Logout clears the browser cookie. In a stateless JWT architecture,
    the client cookie is discarded; for immediate invalidation before expiry,
    a server-side token blacklist or short TTL is recommended.
    """
    settings = get_settings()
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return LogoutResponse(message="Logged out successfully.")


@router.get("/me", response_model=AdminResponse)
def get_current_user_profile(current_admin: dict = Depends(require_admin)):
    """
    Returns the currently authenticated admin profile.
    Used by the frontend to verify active sessions on initial load or navigation.
    """
    return AdminResponse(id=current_admin["id"], email=current_admin["email"])
