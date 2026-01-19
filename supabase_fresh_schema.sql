-- ============================================
-- FRESH SCHEMA: Sheriff Sales with Incremental Tracking
-- Run this in Supabase SQL Editor to recreate all tables
-- WARNING: This will DELETE all existing data!
-- ============================================

-- 1. Drop existing table and related objects
DROP TABLE IF EXISTS sheriff_sales CASCADE;
DROP FUNCTION IF EXISTS append_status_history CASCADE;

-- 2. Create table with all columns
CREATE TABLE sheriff_sales (
    id BIGSERIAL PRIMARY KEY,

    -- Core property info
    county TEXT NOT NULL,
    sheriff_number TEXT,
    court_case_number TEXT,
    status TEXT,
    current_status TEXT,
    sale_date TEXT,

    -- Parties
    plaintiff TEXT,
    defendant TEXT,

    -- Address fields
    address TEXT,
    property_address_full TEXT,
    normalized_address TEXT,

    -- Property details
    description TEXT,
    approx_judgment TEXT,
    upset_amount TEXT,
    minimum_bid TEXT,
    parcel_number TEXT,
    property_note TEXT,

    -- Attorney info
    attorney TEXT,
    attorney_phone TEXT,
    attorney_file_number TEXT,

    -- Status tracking
    status_history JSONB DEFAULT '[]'::JSONB,

    -- Reference
    detail_url TEXT,

    -- Incremental tracking - hashes
    listing_row_hash TEXT,
    detail_hash TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),

    -- Soft delete flag
    is_removed BOOLEAN DEFAULT FALSE
);

-- 3. Create indexes

-- Primary lookup: county + normalized_address (unique)
CREATE UNIQUE INDEX idx_sheriff_sales_county_norm_addr
ON sheriff_sales (county, normalized_address)
WHERE normalized_address IS NOT NULL AND normalized_address != '';

-- Fallback: just normalized_address
CREATE INDEX idx_sheriff_sales_norm_addr
ON sheriff_sales (normalized_address)
WHERE normalized_address IS NOT NULL AND normalized_address != '';

-- Legacy address index
CREATE INDEX idx_sheriff_sales_address ON sheriff_sales (address);

-- County filter
CREATE INDEX idx_sheriff_sales_county ON sheriff_sales (county);

-- Sale date sorting
CREATE INDEX idx_sheriff_sales_sale_date ON sheriff_sales (sale_date);

-- Tombstone queries: stale records per county
CREATE INDEX idx_sheriff_sales_county_last_seen
ON sheriff_sales (county, last_seen_at);

-- Active vs removed filter
CREATE INDEX idx_sheriff_sales_is_removed ON sheriff_sales (is_removed);

-- Hash lookup for change detection
CREATE INDEX idx_sheriff_sales_listing_hash
ON sheriff_sales (listing_row_hash)
WHERE listing_row_hash IS NOT NULL;

-- 4. Create helper function for status history
CREATE OR REPLACE FUNCTION append_status_history(
    existing_history JSONB,
    old_status TEXT,
    new_status TEXT
) RETURNS JSONB AS $$
BEGIN
    IF old_status IS DISTINCT FROM new_status AND new_status IS NOT NULL THEN
        RETURN COALESCE(existing_history, '[]'::JSONB) || jsonb_build_object(
            'at', NOW()::TEXT,
            'from', COALESCE(old_status, ''),
            'to', new_status,
            'source', 'listing+detail'
        );
    END IF;
    RETURN existing_history;
END;
$$ LANGUAGE plpgsql;

-- 5. Enable Row Level Security
ALTER TABLE sheriff_sales ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policy (allow all for service role)
CREATE POLICY "Allow all operations" ON sheriff_sales
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 7. Verify creation
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'sheriff_sales';

    RAISE NOTICE 'Table sheriff_sales created with % columns', col_count;
    RAISE NOTICE 'Ready for scraping!';
END $$;
