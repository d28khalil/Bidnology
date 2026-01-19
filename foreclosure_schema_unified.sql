-- ============================================================================
-- NJ County Foreclosure Listings - Unified Schema
-- salesweb.civilview.com
--
-- This schema is designed to unify 16 NJ Counties' foreclosure data
-- into a single cohesive structure while preserving data integrity.
--
-- Supported Counties:
--   Middlesex (73), Cumberland (6), Gloucester (19), Cape May (52),
--   Camden (1), Burlington (3), Bergen (7), Atlantic (25), Essex (2),
--   Union (15), Salem (20), Monmouth (8), Passaic (17), Morris (9),
--   Hunterdon (32), Hudson (10)
-- ============================================================================

-- ============================================================================
-- Core Property Table (Unified Schema)
-- ============================================================================
CREATE TABLE foreclosure_listings (
    -- Primary Keys
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT UNIQUE NOT NULL,  -- Original PropertyId from source
    county_id SMALLINT NOT NULL,         -- County identifier (1-73, etc.)

    -- Property Identification
    sheriff_number VARCHAR(50),          -- Sheriff # / Sale ID (varies by county)
    case_number VARCHAR(100),            -- Docket/Case number (if available)
    parcel_id VARCHAR(100),              -- Tax/Parcel ID (if available)

    -- Property Address (Structured)
    property_address VARCHAR(500),       -- Full address string
    street_number VARCHAR(50),           -- House/unit number
    street_name VARCHAR(200),            -- Street name
    street_type VARCHAR(20),             -- St, Ave, Rd, etc.
    unit_number VARCHAR(50),             -- Apt, Unit, Condo #
    city VARCHAR(100),                   -- Municipality
    state VARCHAR(2) DEFAULT 'NJ',       -- State
    zip_code VARCHAR(10),                -- ZIP code
    county_name VARCHAR(50),             -- County name for display

    -- Legal Parties
    plaintiff VARCHAR(500),              -- Plaintiff/Lender name
    plaintiff_attorney VARCHAR(500),     -- Plaintiff attorney (if listed)
    defendant VARCHAR(500),              -- Defendant/Property owner
    additional_defendants TEXT[],        -- Multiple defendants as array

    -- ========================================================================
    -- FINANCIAL INFORMATION - IMPORTANT: THREE DISTINCT CATEGORIES
    -- ========================================================================
    -- Category A: Court / Debt Amounts (What Is Owed)
    --   These represent LEGAL DEBT amounts awarded by the court.
    --   They MUST NEVER be used as auction starting bids.
    judgment_amount DECIMAL(12,2),       -- Final Judgment - Court-awarded debt amount
    writ_amount DECIMAL(12,2),           -- Writ Amount - Amount authorized for enforcement
    costs DECIMAL(12,2),                 -- Additional costs/fees

    -- Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
    --   These are the MINIMUM amounts required to initiate bidding.
    --   They MUST NEVER be derived from judgment/writ amounts.
    opening_bid DECIMAL(12,2),           -- Opening Bid - Minimum bid to start auction
    minimum_bid DECIMAL(12,2),           -- Minimum Bid - Alias for opening bid

    -- Category C: Estimated / Approximate Amounts (Non-Authoritative)
    --   These are APPROXIMATE values for reference only.
    --   They MUST NEVER overwrite authoritative sale/auction data.
    approx_upset DECIMAL(12,2),          -- Approx Upset - Estimated opening bid (Essex County)

    -- Final Sale Data
    sale_price DECIMAL(12,2),            -- Final sale price (if sold)

    -- Sale/Schedule Information
    sale_date DATE,                      -- Scheduled/Auction date
    sale_time TIME,                      -- Auction time (if specified)
    property_status VARCHAR(50),         -- Open/Sold/Cancelled/Adjourned
    status_detail VARCHAR(100),          -- Adjourned - Plaintiff/Court/Defendant

    -- Property Details
    property_type VARCHAR(50),           -- Residential/Commercial/Vacant Land
    lot_size VARCHAR(50),                -- Lot dimensions/acreage
    property_description TEXT,           -- Legal description/notes

    -- Legal Proceedings
    court_name VARCHAR(200),             -- Superior Court of NJ, County
    filing_date DATE,                    -- Original filing date
    judgment_date DATE,                  -- Judgment entry date
    writ_date DATE,                      -- Writ of execution date

    -- Additional Information
    sale_terms TEXT,                     -- Special terms/conditions
    attorney_notes TEXT,                 -- Notes from attorney office
    general_notes TEXT,                  -- Miscellaneous notes

    -- System Fields
    data_source_url VARCHAR(500),        -- URL to original listing
    raw_data JSONB,                      -- Store original scraped data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_synced_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_county_id CHECK (county_id IN (1, 2, 3, 6, 7, 8, 9, 10, 15, 17, 19, 20, 25, 32, 52, 73))
);

-- Indexes for common queries
CREATE INDEX idx_foreclosure_county ON foreclosure_listings(county_id);
CREATE INDEX idx_foreclosure_sheriff_num ON foreclosure_listings(sheriff_number);
CREATE INDEX idx_foreclosure_sale_date ON foreclosure_listings(sale_date);
CREATE INDEX idx_foreclosure_city ON foreclosure_listings(city);
CREATE INDEX idx_foreclosure_status ON foreclosure_listings(property_status);
CREATE INDEX idx_foreclosure_defendant ON foreclosure_listings(defendant);
CREATE INDEX idx_foreclosure_plaintiff ON foreclosure_listings(plaintiff);
CREATE INDEX idx_foreclosure_county_date ON foreclosure_listings(county_id, sale_date);

-- Full-text search for addresses and names
CREATE INDEX idx_foreclosure_address_fts ON foreclosure_listings USING gin(to_tsvector('english', property_address));
CREATE INDEX idx_foreclosure_defendant_fts ON foreclosure_listings USING gin(to_tsvector('english', defendant));
CREATE INDEX idx_foreclosure_plaintiff_fts ON foreclosure_listings USING gin(to_tsvector('english', plaintiff));

-- ============================================================================
-- County Field Mappings Table (Handles county-specific field variations)
-- ============================================================================
CREATE TABLE county_field_mappings (
    id SERIAL PRIMARY KEY,
    county_id SMALLINT NOT NULL,
    county_name VARCHAR(50) NOT NULL,
    source_field_name VARCHAR(100) NOT NULL,  -- Original field name from county
    unified_field_name VARCHAR(100) NOT NULL, -- Maps to foreclosure_listings column
    data_type VARCHAR(20) NOT NULL,           -- varchar, decimal, date, etc.
    is_required BOOLEAN DEFAULT FALSE,
    transformation_rules TEXT,                 -- SQL/transform logic if needed
    notes TEXT,

    CONSTRAINT unique_county_field UNIQUE (county_id, source_field_name)
);

-- ============================================================================
-- County Metadata Table
-- ============================================================================
CREATE TABLE counties (
    county_id SMALLINT PRIMARY KEY,
    county_name VARCHAR(50) UNIQUE NOT NULL,
    state VARCHAR(2) DEFAULT 'NJ',
    sheriff_id_prefix VARCHAR(10),            -- F-, FR-, L-, or none
    base_url VARCHAR(200),
    search_url VARCHAR(200),
    active BOOLEAN DEFAULT TRUE,
    scraper_config JSONB,                     -- County-specific scraper settings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Scraping Log Table (Audit trail)
-- ============================================================================
CREATE TABLE scraping_logs (
    id BIGSERIAL PRIMARY KEY,
    county_id SMALLINT NOT NULL,
    scrape_type VARCHAR(50) NOT NULL,         -- 'listing', 'details', 'full'
    status VARCHAR(20) NOT NULL,              -- 'success', 'partial', 'failed'
    records_found INTEGER DEFAULT 0,
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    error_messages TEXT[],
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    scrape_metadata JSONB
);

-- ============================================================================
-- Property History/Audit Table (Track changes to listings)
-- ============================================================================
CREATE TABLE foreclosure_history (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL,              -- Reference to foreclosure_listings.id
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_type VARCHAR(20) NOT NULL,         -- 'insert', 'update', 'status_change'
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) DEFAULT 'scraper'
);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- Active listings (scheduled for future sale)
CREATE VIEW active_foreclosures AS
SELECT
    id,
    sheriff_number,
    county_name,
    property_address,
    city,
    sale_date,
    plaintiff,
    defendant,
    property_status,
    opening_bid
FROM foreclosure_listings
WHERE property_status IN ('Open', 'Scheduled - Foreclosure', 'Scheduled')
  AND sale_date >= CURRENT_DATE
ORDER BY sale_date, county_name;

-- Recent sales (sold/foreclosed properties)
CREATE VIEW recent_sales AS
SELECT
    id,
    sheriff_number,
    county_name,
    property_address,
    city,
    sale_date,
    plaintiff,
    defendant,
    sale_price,
    property_status
FROM foreclosure_listings
WHERE property_status IN ('Sold', 'Sold/Cancelled', 'Sold-Cancelled')
  AND sale_date >= (CURRENT_DATE - INTERVAL '90 days')
ORDER BY sale_date DESC;

-- County statistics
CREATE VIEW county_statistics AS
SELECT
    county_id,
    county_name,
    COUNT(*) as total_listings,
    COUNT(*) FILTER (WHERE property_status IN ('Open', 'Scheduled')) as active_listings,
    COUNT(*) FILTER (WHERE property_status = 'Sold') as sold_count,
    COUNT(*) FILTER (WHERE property_status LIKE 'Adjourned%') as adjourned_count,
    SUM(opening_bid) FILTER (WHERE opening_bid IS NOT NULL) as total_opening_bids,
    MAX(sale_date) as latest_sale_date
FROM foreclosure_listings
GROUP BY county_id, county_name
ORDER BY county_name;

-- ============================================================================
-- County-Specific Status Values (helps normalize status variations)
-- ============================================================================
CREATE TYPE foreclosure_status AS ENUM (
    'scheduled',           -- Scheduled for sale
    'adjourned_plaintiff', -- Adjourned by Plaintiff
    'adjourned_court',     -- Adjourned by Court
    'adjourned_defendant', -- Adjourned by Defendant
    'sold',                -- Property sold
    'cancelled',           -- Sale cancelled
    'withdrawn',           -- Case withdrawn
    'unknown'              -- Status unknown
);

-- Status mapping table (county-specific statuses to unified enum)
CREATE TABLE status_mappings (
    id SERIAL PRIMARY KEY,
    county_id SMALLINT NOT NULL,
    raw_status_text VARCHAR(100) NOT NULL,  -- Original status from county
    unified_status foreclosure_status NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Parse address into components
CREATE OR REPLACE FUNCTION parse_address(full_address TEXT)
RETURNS TABLE(
    street_number VARCHAR(50),
    street_name VARCHAR(200),
    unit_number VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10)
) AS $$
BEGIN
    -- This is a placeholder - implement based on your address parsing needs
    -- You may want to use a PostGIS extension or external service
    RETURN QUERY
    SELECT
        substring(full_address FROM '^(\d+[A-Z]?)') as street_number,
        substring(full_address FROM '\d+[A-Z]?\s+([^,]+)') as street_name,
        substring(full_address FROM '(Unit|Apt|Cond|#\s+[^\s,]+)') as unit_number,
        substring(full_address FROM '([^,]+)\s+[A-Z]{2}') as city,
        substring(full_address FROM '\s([A-Z]{2})\s') as state,
        substring(full_address FROM '(\d{5}(?:-\d{4})?)$') as zip_code;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_foreclosure_listings_updated_at
    BEFORE UPDATE ON foreclosure_listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_counties_updated_at
    BEFORE UPDATE ON counties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE foreclosure_listings IS 'Unified foreclosure listings from all NJ counties';
COMMENT ON TABLE county_field_mappings IS 'Maps county-specific field names to unified schema';
COMMENT ON TABLE counties IS 'Metadata for each county including scraper configuration';
COMMENT ON TABLE scraping_logs IS 'Audit log for all scraping operations';
COMMENT ON TABLE foreclosure_history IS 'Change history for individual property listings';
COMMENT ON TABLE status_mappings IS 'Maps county-specific status text to unified status enum';

COMMENT ON COLUMN foreclosure_listings.raw_data IS 'Store original scraped JSON for reference and debugging';
COMMENT ON COLUMN counties.scraper_config IS 'JSON configuration for county-specific scraping logic';
