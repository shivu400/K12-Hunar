import getpass
import sys
from psycopg import connect
from psycopg.rows import dict_row

from app.config import get_settings
from app.queries.admins import get_admin_by_email, insert_admin
from app.security import hash_password


def main():
    """
    CLI provisioning script to create an initial or new administrator.
    Reads credentials from command-line/terminal prompts or fallback environment variables.
    Hashes password using bcrypt (with 72-byte limit safety).
    Handles existing admin email gracefully without crashing.
    """
    print("=" * 60)
    print("EdTech CRM - Secure Admin Provisioning CLI")
    print("=" * 60)

    settings = get_settings()

    # Determine email
    email = None
    if settings.ADMIN_EMAIL:
        email = settings.ADMIN_EMAIL.strip()
    else:
        email = input("Enter admin email address: ").strip()

    if not email or "@" not in email:
        print("Error: A valid email address is required.")
        sys.exit(1)

    # Determine password
    password = None
    if settings.ADMIN_PASSWORD:
        password = settings.ADMIN_PASSWORD
        print(f"Using ADMIN_PASSWORD from environment for: {email}")
    else:
        password = getpass.getpass("Enter secure admin password: ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        if password != confirm_password:
            print("Error: Passwords do not match.")
            sys.exit(1)

    if len(password.encode("utf-8")) > 72:
        print("Error: Password cannot exceed 72 bytes (bcrypt restriction).")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    print("\nConnecting to PostgreSQL database...")
    try:
        with connect(settings.DATABASE_URL, row_factory=dict_row) as conn:
            existing = get_admin_by_email(conn, email)
            if existing:
                print(f"Notice: Admin with email '{email}' already exists (ID: {existing['id']}).")
                print("No duplicate user was created. To update the password, use an UPDATE statement.")
                sys.exit(0)

            hashed_pwd = hash_password(password)
            created = insert_admin(conn, email, hashed_pwd)
            print(f"Success! Admin created successfully.")
            print(f"Admin ID:    {created['id']}")
            print(f"Email:       {created['email']}")
            print(f"Created At:  {created['created_at']}")
            print("=" * 60)
    except Exception as exc:
        print(f"Database error during admin provisioning: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
