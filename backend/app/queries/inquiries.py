from psycopg import Connection
from app.schemas.inquiries import InquiryCreate


def create_inquiry(conn: Connection, inquiry: InquiryCreate) -> dict:
    """
    Inserts a new inquiry into PostgreSQL using parameterized SQL.
    Defaults status to 'New'.
    """
    query = """
        INSERT INTO inquiries (user_type, category, name, email, phone, message, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'New')
        RETURNING id, user_type, category, name, email, phone, message, status, created_at, updated_at;
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                inquiry.user_type,
                inquiry.category,
                inquiry.name,
                inquiry.email,
                inquiry.phone,
                inquiry.message,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        row["id"] = str(row["id"])
        return row


def get_inquiry_by_id(conn: Connection, inquiry_id: str) -> dict | None:
    """
    Fetches a single inquiry by its UUID.
    """
    query = """
        SELECT id, user_type, category, name, email, phone, message, status, created_at, updated_at
        FROM inquiries
        WHERE id = %s
        LIMIT 1;
    """
    with conn.cursor() as cur:
        cur.execute(query, (inquiry_id,))
        row = cur.fetchone()
        if row:
            row["id"] = str(row["id"])
            return row
        return None


def list_inquiries(
    conn: Connection,
    category: str | None = None,
    user_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    """
    Lists inquiries with mandatory dynamic filtering, search by name or phone,
    and server-side pagination with stable sorting (created_at DESC, id DESC).
    All filters and search values are strictly parameterized.
    """
    where_clauses: list[str] = []
    params: list[object] = []

    if category:
        where_clauses.append("category = %s")
        params.append(category)

    if user_type:
        where_clauses.append("user_type = %s")
        params.append(user_type)

    if search:
        search_term = f"%{search.strip()}%"
        # Search by name OR phone number
        where_clauses.append("(name ILIKE %s OR phone ILIKE %s)")
        params.extend([search_term, search_term])

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(*) AS total FROM inquiries {where_sql};"

    offset = (page - 1) * limit
    data_query = f"""
        SELECT id, user_type, category, name, email, phone, message, status, created_at, updated_at
        FROM inquiries
        {where_sql}
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s;
    """

    with conn.cursor() as cur:
        # Get count
        cur.execute(count_query, params)
        count_res = cur.fetchone()
        total = count_res["total"] if count_res else 0

        # Get paginated data
        query_params = list(params) + [limit, offset]
        cur.execute(data_query, query_params)
        rows = cur.fetchall()

        for r in rows:
            r["id"] = str(r["id"])

        return rows, total


def update_inquiry_status(conn: Connection, inquiry_id: str, new_status: str) -> dict | None:
    """
    Updates the inquiry status and sets updated_at = CURRENT_TIMESTAMP.
    Returns the updated record or None if inquiry does not exist.
    """
    query = """
        UPDATE inquiries
        SET status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, user_type, category, name, email, phone, message, status, created_at, updated_at;
    """
    with conn.cursor() as cur:
        cur.execute(query, (new_status, inquiry_id))
        row = cur.fetchone()
        conn.commit()
        if row:
            row["id"] = str(row["id"])
            return row
        return None
