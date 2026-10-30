from psycopg import Connection


def get_admin_by_email(conn: Connection, email: str) -> dict | None:
    """
    Fetches an admin by case-insensitive email match.
    Uses parameterized SQL to prevent SQL injection.
    """
    query = """
        SELECT id, email, password_hash, created_at
        FROM admins
        WHERE LOWER(email) = LOWER(%s)
        LIMIT 1;
    """
    with conn.cursor() as cur:
        cur.execute(query, (email.strip(),))
        row = cur.fetchone()
        if row:
            # Cast id to str for consistency
            row["id"] = str(row["id"])
            return row
        return None


def get_admin_by_id(conn: Connection, admin_id: str) -> dict | None:
    """
    Fetches an admin by UUID id.
    """
    query = """
        SELECT id, email, created_at
        FROM admins
        WHERE id = %s
        LIMIT 1;
    """
    with conn.cursor() as cur:
        cur.execute(query, (admin_id,))
        row = cur.fetchone()
        if row:
            row["id"] = str(row["id"])
            return row
        return None


def insert_admin(conn: Connection, email: str, password_hash: str) -> dict:
    """
    Inserts a newly provisioned admin with parameterized SQL.
    Returns the created record.
    """
    query = """
        INSERT INTO admins (email, password_hash)
        VALUES (%s, %s)
        RETURNING id, email, created_at;
    """
    with conn.cursor() as cur:
        cur.execute(query, (email.strip().lower(), password_hash))
        row = cur.fetchone()
        conn.commit()
        row["id"] = str(row["id"])
        return row
