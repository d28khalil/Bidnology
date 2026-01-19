-- Sheriff Sales Table Schema for Supabase
-- Run this in your Supabase SQL Editor to create the table

CREATE TABLE IF NOT EXISTS sheriff_sales (
    id BIGSERIAL PRIMARY KEY,

    -- Core property info
    county TEXT,
    sheriff_number TEXT,
    court_case_number TEXT,
    status TEXT,
    current_status TEXT,
    sale_date TEXT,

    -- Parties
    plaintiff TEXT,
    defendant TEXT,

    -- Address (used for duplicate detection)
    address TEXT,
    property_address_full TEXT,

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
    status_history JSONB,

    -- Reference
    detail_url TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on address for fast duplicate lookups
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_address ON sheriff_sales (address);

-- Create index on county for filtering
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_county ON sheriff_sales (county);

-- Create index on sale_date for sorting/filtering
CREATE INDEX IF NOT EXISTS idx_sheriff_sales_sale_date ON sheriff_sales (sale_date);

-- Optional: Add unique constraint on address to prevent duplicates at DB level
-- Uncomment if you want database-level duplicate prevention
-- ALTER TABLE sheriff_sales ADD CONSTRAINT unique_address UNIQUE (address);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE sheriff_sales ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (adjust based on your needs)
CREATE POLICY "Allow all operations" ON sheriff_sales
    FOR ALL
    USING (true)
    WITH CHECK (true);
