import os
import sys
import psycopg
from psycopg import sql

# Target connection details from backend/.env
DB_USER = "postgres"
DB_PASS = "Lenovo@12"
DB_HOST = "localhost"
DB_PORT = 5432
TARGET_DB = "edtech_crm"

def setup():
    print("=" * 60)
    print("Step 1: Connecting to PostgreSQL server on localhost:5432...")
    print("=" * 60)
    
    # 1. Connect to default 'postgres' maintenance database
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname="postgres",
            autocommit=True
        )
        print(" Connected successfully to PostgreSQL server!")
    except Exception as e:
        print(f"\n❌ Could not connect to PostgreSQL on localhost:5432.")
        print(f"Error details: {e}\n")
        print("Please check:")
        print("1. Is PostgreSQL service running in Windows Services? (Win + R -> services.msc -> postgresql-x64)")
        print("2. Is the password 'Lenovo@12' correct?")
        sys.exit(1)

    # 2. Check if 'edtech_crm' database exists, create if not
    print("\n" + "=" * 60)
    print(f"Step 2: Checking if database '{TARGET_DB}' exists...")
    print("=" * 60)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
            exists = cur.fetchone()
            if not exists:
                print(f"Creating database '{TARGET_DB}'...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TARGET_DB)))
                print(f" Database '{TARGET_DB}' created successfully!")
            else:
                print(f" Database '{TARGET_DB}' already exists.")
        conn.close()
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.close()
        sys.exit(1)

    # 3. Connect to 'edtech_crm' and run schema.sql
    print("\n" + "=" * 60)
    print(f"Step 3: Applying schema.sql to '{TARGET_DB}'...")
    print("=" * 60)
    # schema.sql is at the root project directory (parent of backend)
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schema.sql")
    if not os.path.exists(schema_path):
        # Fallback check
        schema_path = os.path.abspath(os.path.join(os.getcwd(), "..", "schema.sql"))
        if not os.path.exists(schema_path):
            schema_path = os.path.abspath(os.path.join(os.getcwd(), "schema.sql"))
        print(f"❌ Could not find schema.sql at {schema_path}")
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    try:
        with psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=TARGET_DB,
            autocommit=True
        ) as app_conn:
            with app_conn.cursor() as cur:
                cur.execute(schema_sql)
        print(" schema.sql applied successfully! All tables, indexes, and constraints are ready.")
    except Exception as e:
        print(f"❌ Error applying schema.sql: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" PostgreSQL Setup Complete!")
    print("=" * 60)
    print("Next step: Run 'python -m scripts.create_admin' to create your admin user.")

if __name__ == "__main__":
    setup()

