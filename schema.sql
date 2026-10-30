-- EdTech CRM and Inquiry System - Schema
-- PostgreSQL DDL for Supabase / PostgreSQL 14+

-- 1. Enable pgcrypto or uuid-ossp if UUID generation is needed
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Create custom enum or check constraints
-- We use CHECK constraints on VARCHAR/TEXT for transparency, ease of migration, and seamless Pydantic/SQL mapping.

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Case-insensitive unique index for admin email
CREATE UNIQUE INDEX IF NOT EXISTS idx_admins_email_lower ON admins (LOWER(email));

-- Inquiries Table
CREATE TABLE IF NOT EXISTS inquiries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('Parent', 'Student', 'School')),
    category VARCHAR(50) NOT NULL CHECK (category IN ('Scholarship', 'Concert', 'Admission', 'General Query')),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'New' CHECK (status IN ('New', 'In Progress', 'Resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance and assessment query patterns:
-- 1. Index on created_at DESC for primary default sorting
CREATE INDEX IF NOT EXISTS idx_inquiries_created_at_desc ON inquiries (created_at DESC, id DESC);

-- 2. Indexes for mandatory equality filters
CREATE INDEX IF NOT EXISTS idx_inquiries_category ON inquiries (category);
CREATE INDEX IF NOT EXISTS idx_inquiries_user_type ON inquiries (user_type);
CREATE INDEX IF NOT EXISTS idx_inquiries_status ON inquiries (status);

-- 3. Composite index for combined category & user_type filters with order
CREATE INDEX IF NOT EXISTS idx_inquiries_cat_ut_created ON inquiries (category, user_type, created_at DESC);

-- Note on Search:
-- Standard B-tree indexes accelerate exact matches or prefix matching (LIKE 'term%').
-- For arbitrary substring search (ILIKE '%term%'), full-table scans or pg_trgm trigram indexes are required.
-- On assessment scale data (<100k rows), parameterized B-tree or scan is fast and robust.
-- For production high-volume trigram acceleration, pg_trgm GIN index can be added:
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_inquiries_name_trgm ON inquiries USING gin (name gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_inquiries_phone_trgm ON inquiries USING gin (phone gin_trgm_ops);

-- Row Level Security (RLS) note:
-- In Supabase, 'anon' role is present by default.
-- On local vanilla PostgreSQL, create role 'anon' if it does not exist before applying policy.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
END
$$;

ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Deny anon access on admins" ON admins;
CREATE POLICY "Deny anon access on admins" ON admins FOR ALL TO anon USING (false);

DROP POLICY IF EXISTS "Deny anon access on inquiries" ON inquiries;
CREATE POLICY "Deny anon access on inquiries" ON inquiries FOR ALL TO anon USING (false);
