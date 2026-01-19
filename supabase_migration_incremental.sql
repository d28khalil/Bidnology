-- Migration: Add incremental tracking columns for change detection
-- Run this in Supabase SQL Editor after the initial schema

-- ============================================
-- 1. Add new columns for incremental tracking
-- ============================================

-- Normalized address for consistent duplicate detection
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS normalized_address TEXT;

-- Hash of listing row data (detects changes without clicking details)
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS listing_row_hash TEXT;

-- Hash of detail page data (optional, for deeper change tracking)
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS detail_hash TEXT;

-- Tracking timestamps
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW();

-- Soft delete flag (never hard delete)
ALTER TABLE sheriff_sales
ADD COLUMN IF NOT EXISTS is_removed BOOLEAN DEFAULT FALSE;

-- ============================================
-- 2. Create indexes for efficient lookups
-- ============================================

-- Primary lookup: county + normalized_address (unique constraint)
CREATE UNIQUE INDEX IF NOT EXISTS idx_sheriff_sales_county_norm_addr
ON sheriff_sales (county, normalized_address)
WHERE normalized_address IS NOT NULL AND normalized_address != '';

-- Fallback lookup: just normalized_address
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_norm_addr
ON sheriff_sales (normalized_address)
WHERE normalized_address IS NOT NULL AND normalized_address != '';

-- For tombstone queries: find stale records per county
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_county_last_seen
ON sheriff_sales (county, last_seen_at);

-- For filtering active vs removed
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_is_removed
ON sheriff_sales (is_removed);

-- Hash lookup for quick change detection
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_listing_hash
ON sheriff_sales (listing_row_hash)
WHERE listing_row_hash IS NOT NULL;

-- ============================================
-- 3. Backfill normalized_address for existing rows
-- ============================================

-- Normalize: lowercase, trim, collapse whitespace
UPDATE sheriff_sales
SET normalized_address = LOWER(TRIM(REGEXP_REPLACE(address, '\s+', ' ', 'g')))
WHERE normalized_address IS NULL
  AND address IS NOT NULL
  AND address != '';

-- Set first_seen_at for existing rows that don't have it
UPDATE sheriff_sales
SET first_seen_at = COALESCE(created_at, NOW())
WHERE first_seen_at IS NULL;

-- Set last_seen_at for existing rows
UPDATE sheriff_sales
SET last_seen_at = COALESCE(updated_at, created_at, NOW())
WHERE last_seen_at IS NULL;

-- ============================================
-- 4. Create function for upsert operations
-- ============================================

-- Function to handle status history appending
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

-- ============================================
-- 5. Verify migration
-- ============================================

-- Check columns exist
DO $$
BEGIN
    RAISE NOTICE 'Migration complete. Verifying columns...';

    PERFORM column_name
    FROM information_schema.columns
    WHERE table_name = 'sheriff_sales'
      AND column_name IN ('normalized_address', 'listing_row_hash', 'detail_hash',
                          'first_seen_at', 'last_seen_at', 'is_removed');

    RAISE NOTICE 'All incremental tracking columns verified.';
END $$;
