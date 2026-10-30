from fastapi import Depends, HTTPException, Request, status
from psycopg import Connection
from app.database import get_db_connection
from app.security import decode_access_token
from app.queries.admins import get_admin_by_id

AUTH_COOKIE_NAME = "edtech_token"


def get_current_admin(
    request: Request,
    conn: Connection = Depends(get_db_connection),
) -> dict:
    """
    FastAPI dependency that extracts and verifies JWT from HttpOnly cookie.
    Rejects unauthenticated or invalid sessions with 401 Unauthorized.
    """
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        # Also check Authorization header as a fallback for API tooling/clients
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )

    admin_id = payload["sub"]
    admin = get_admin_by_id(conn, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account no longer exists.",
        )
    return admin

    return admin


def require_admin(admin: dict = Depends(get_current_admin)) -> dict:
    """
    Explicit alias dependency used across protected routes.
    """
    return admin
