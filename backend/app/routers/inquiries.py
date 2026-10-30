from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from app.database import get_db_connection
from app.dependencies import require_admin
from app.queries.inquiries import (
    create_inquiry,
    get_inquiry_by_id,
    list_inquiries,
    update_inquiry_status,
)
from app.schemas.inquiries import (
    CategoryEnum,
    InquiryCreate,
    InquiryListResponse,
    InquiryResponse,
    InquiryStatusUpdate,
    UserTypeEnum,
)

router = APIRouter(prefix="/api/inquiries", tags=["Inquiries"])


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_public_inquiry(
    payload: InquiryCreate,
    conn: Connection = Depends(get_db_connection),
):
    """
    Public endpoint to submit a new inquiry.
    Validates input, trims appropriate text, enforces constraints, and stores in PostgreSQL.
    """
    try:
        created = create_inquiry(conn, payload)
        return created
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit inquiry. Please try again later.",
        ) from exc


@router.get("", response_model=InquiryListResponse)
def get_inquiries_dashboard(
    category: CategoryEnum | None = Query(None, description="Filter by category"),
    user_type: UserTypeEnum | None = Query(None, alias="userType", description="Filter by user type"),
    search: str | None = Query(None, description="Search by name or phone"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    conn: Connection = Depends(get_db_connection),
    current_admin: dict = Depends(require_admin),
):
    """
    Protected endpoint: Retrieves paginated inquiries with dynamic category, userType,
    and search filtering. Enforces admin authentication via require_admin.
    """
    items, total = list_inquiries(
        conn=conn,
        category=category,
        user_type=user_type,
        search=search,
        page=page,
        limit=limit,
    )
    total_pages = ceil(total / limit) if total > 0 else 1

    return InquiryListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry_detail(
    inquiry_id: str,
    conn: Connection = Depends(get_db_connection),
    current_admin: dict = Depends(require_admin),
):
    """
    Protected endpoint: View the full inquiry details including multiline message.
    """
    inquiry = get_inquiry_by_id(conn, inquiry_id)
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found.",
        )
    return inquiry


@router.patch("/{inquiry_id}/status", response_model=InquiryResponse)
def patch_inquiry_status(
    inquiry_id: str,
    payload: InquiryStatusUpdate,
    conn: Connection = Depends(get_db_connection),
    current_admin: dict = Depends(require_admin),
):
    """
    Protected endpoint: Update the status of an inquiry ('New', 'In Progress', 'Resolved').
    """
    updated = update_inquiry_status(conn, inquiry_id, payload.status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found.",
        )
    return updated
