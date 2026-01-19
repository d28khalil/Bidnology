-- ============================================================================
-- NJ County Foreclosure Field Mappings Guide
-- ============================================================================
-- This document provides field mappings for all 16 NJ Counties to help
-- your scraper translate county-specific field names to the unified schema.
--
-- CRITICAL MONETARY FIELD CATEGORIES:
-- ====================================
-- Category A: Court / Debt Amounts (What Is Owed)
--   - judgment_amount: Final Judgment, Judgment Amount (COURT-awarded debt)
--   - writ_amount: Writ Amount, Writ of Execution (amount authorized for enforcement)
--   - NOTE: These MUST NEVER be used as auction starting bids
--
-- Category B: Auction / Sale Floor Amounts (What Bidding Starts At)
--   - opening_bid: Opening Bid, Minimum Bid, Starting Bid, Upset Price
--   - minimum_bid: Alias for opening_bid
--   - NOTE: These MUST NEVER be derived from judgment/writ amounts
--
-- Category C: Estimated / Approximate Amounts (Non-Authoritative)
--   - approx_upset: Approx Upset, Approx. Upset (Essex County)
--   - NOTE: These are REFERENCE ONLY, never overwrite authoritative data
--
-- Design Rules (Non-Negotiable):
--   1. Court/debt amounts MUST NEVER be used as auction starting bids
--   2. Auction floor amounts MUST NEVER be derived from judgment values
--   3. Approximate values MUST remain separate from authoritative sale data
--
-- Usage: Populate the county_field_mappings table with these mappings
-- ============================================================================

-- ============================================================================
-- INSERT COUNTY METADATA
-- ============================================================================

INSERT INTO counties (county_id, county_name, sheriff_id_prefix, search_url) VALUES
(1, 'Camden', 'FR-', '/Sales/SalesSearch?countyId=1'),
(2, 'Essex', 'F-', '/Sales/SalesSearch?countyId=2'),
(3, 'Burlington', NULL, '/Sales/SalesSearch?countyId=3'),
(6, 'Cumberland', 'F-', '/Sales/SalesSearch?countyId=6'),
(7, 'Bergen', 'F-', '/Sales/SalesSearch?countyId=7'),
(8, 'Monmouth', 'F-', '/Sales/SalesSearch?countyId=8'),
(9, 'Morris', 'F-', '/Sales/SalesSearch?countyId=9'),
(10, 'Hudson', 'F-', '/Sales/SalesSearch?countyId=10'),
(15, 'Union', 'F-', '/Sales/SalesSearch?countyId=15'),
(17, 'Passaic', 'F-', '/Sales/SalesSearch?countyId=17'),
(19, 'Gloucester', 'F-', '/Sales/SalesSearch?countyId=19'),
(20, 'Salem', 'F-', '/Sales/SalesSearch?countyId=20'),
(25, 'Atlantic', 'F-', '/Sales/SalesSearch?countyId=25'),
(32, 'Hunterdon', 'F-', '/Sales/SalesSearch?countyId=32'),
(52, 'Cape May', 'F-', '/Sales/SalesSearch?countyId=52'),
(73, 'Middlesex', 'F-', '/Sales/SalesSearch?countyId=73');

-- ============================================================================
-- ATLANTIC COUNTY (ID: 25) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
-- Search Page Fields
(25, 'Atlantic', 'SheriffNumber', 'sheriff_number', 'varchar'),
(25, 'Atlantic', 'Sheriff #', 'sheriff_number', 'varchar'),
(25, 'Atlantic', 'Sales Date', 'sale_date', 'date'),
(25, 'Atlantic', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(25, 'Atlantic', 'Plaintiff', 'plaintiff', 'varchar'),
(25, 'Atlantic', 'DefendantTitle', 'defendant', 'varchar'),
(25, 'Atlantic', 'Defendant', 'defendant', 'varchar'),
(25, 'Atlantic', 'Address', 'property_address', 'varchar'),
(25, 'Atlantic', 'CityDesc', 'city', 'varchar'),

-- Details Page Fields (Atlantic-specific)
(25, 'Atlantic', 'PropertyId', 'property_id', 'bigint'),
(25, 'Atlantic', 'Address (continued)', 'property_address', 'varchar'),
(25, 'Atlantic', 'Plaintiff Attorney', 'plaintiff_attorney', 'varchar'),

-- Atlantic County Monetary Fields - Category A: Court/Debt Amounts
(25, 'Atlantic', 'Writ Amount', 'writ_amount', 'decimal'),
(25, 'Atlantic', 'Writ of Execution', 'writ_amount', 'decimal'),
(25, 'Atlantic', 'Final Judgment', 'judgment_amount', 'decimal'),
(25, 'Atlantic', 'Judgment Amount', 'judgment_amount', 'decimal'),
(25, 'Atlantic', 'Costs', 'costs', 'decimal'),

-- Atlantic County Monetary Fields - Category B: Auction/Sale Floor Amounts
(25, 'Atlantic', 'Sale Amount', 'opening_bid', 'decimal'),
(25, 'Atlantic', 'Opening Bid', 'opening_bid', 'decimal'),
(25, 'Atlantic', 'Minimum Bid', 'opening_bid', 'decimal');

-- ============================================================================
-- MIDDLESEX COUNTY (ID: 73) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
-- Search Page Fields (Middlesex includes Status column)
(73, 'Middlesex', 'SheriffNumber', 'sheriff_number', 'varchar'),
(73, 'Middlesex', 'Sheriff #', 'sheriff_number', 'varchar'),
(73, 'Middlesex', 'Status', 'property_status', 'varchar'),
(73, 'Middlesex', 'Sales Date', 'sale_date', 'date'),
(73, 'Middlesex', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(73, 'Middlesex', 'Plaintiff', 'plaintiff', 'varchar'),
(73, 'Middlesex', 'DefendantTitle', 'defendant', 'varchar'),
(73, 'Middlesex', 'Defendant', 'defendant', 'varchar'),
(73, 'Middlesex', 'Address', 'property_address', 'varchar'),
(73, 'Middlesex', 'CityDesc', 'city', 'varchar'),

-- Details Page Fields (Middlesex-specific variations)
(73, 'Middlesex', 'Docket Number', 'case_number', 'varchar'),
(73, 'Middlesex', 'Case No.', 'case_number', 'varchar'),
(73, 'Middlesex', 'Attorney for Plaintiff', 'plaintiff_attorney', 'varchar'),
(73, 'Middlesex', 'Plaintiff''s Attorney', 'plaintiff_attorney', 'varchar'),

-- Middlesex County Monetary Fields - Category A: Court/Debt Amounts
(73, 'Middlesex', 'Final Judgment', 'judgment_amount', 'decimal'),
(73, 'Middlesex', 'Judgment Amount', 'judgment_amount', 'decimal'),
(73, 'Middlesex', 'Writ Amount', 'writ_amount', 'decimal'),
(73, 'Middlesex', 'Writ of Execution', 'writ_amount', 'decimal'),

-- Middlesex County Monetary Fields - Category B: Auction/Sale Floor Amounts
(73, 'Middlesex', 'Opening Bid', 'opening_bid', 'decimal'),
(73, 'Middlesex', 'Minimum Bid', 'opening_bid', 'decimal'),

-- Middlesex County Final Sale Data
(73, 'Middlesex', 'Sale Price', 'sale_price', 'decimal');

-- ============================================================================
-- CAPE MAY COUNTY (ID: 52) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(52, 'Cape May', 'SheriffNumber', 'sheriff_number', 'varchar'),
(52, 'Cape May', 'Sheriff #', 'sheriff_number', 'varchar'),
(52, 'Cape May', 'Sales Date', 'sale_date', 'date'),
(52, 'Cape May', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(52, 'Cape May', 'Plaintiff', 'plaintiff', 'varchar'),
(52, 'Cape May', 'DefendantTitle', 'defendant', 'varchar'),
(52, 'Cape May', 'Defendant', 'defendant', 'varchar'),
(52, 'Cape May', 'Address', 'property_address', 'varchar'),
(52, 'Cape May', 'CityDesc', 'city', 'varchar'),

-- Cape May County Monetary Fields - Category A: Court/Debt Amounts
(52, 'Cape May', 'Writ of Execution', 'writ_amount', 'decimal'),
(52, 'Cape May', 'Writ Amount', 'writ_amount', 'decimal'),
(52, 'Cape May', 'Final Judgment', 'judgment_amount', 'decimal'),
(52, 'Cape May', 'Judgment Amount', 'judgment_amount', 'decimal'),

-- Cape May County Monetary Fields - Category B: Auction/Sale Floor Amounts
(52, 'Cape May', 'Upset Price', 'opening_bid', 'decimal'),
(52, 'Cape May', 'Minimum Bid', 'opening_bid', 'decimal'),
(52, 'Cape May', 'Opening Bid', 'opening_bid', 'decimal'),

-- Cape May County Final Sale Data
(52, 'Cape May', 'Sale Price', 'sale_price', 'decimal');

-- ============================================================================
-- BERGEN COUNTY (ID: 7) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(7, 'Bergen', 'SheriffNumber', 'sheriff_number', 'varchar'),
(7, 'Bergen', 'Sheriff #', 'sheriff_number', 'varchar'),
(7, 'Bergen', 'Sales Date', 'sale_date', 'date'),
(7, 'Bergen', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(7, 'Bergen', 'Plaintiff', 'plaintiff', 'varchar'),
(7, 'Bergen', 'DefendantTitle', 'defendant', 'varchar'),
(7, 'Bergen', 'Defendant', 'defendant', 'varchar'),
(7, 'Bergen', 'Address', 'property_address', 'varchar'),
(7, 'Bergen', 'CityDesc', 'city', 'varchar'),
(7, 'Bergen', 'Docket #', 'case_number', 'varchar'),
(7, 'Bergen', 'Judgment', 'judgment_amount', 'decimal'),
(7, 'Bergen', 'Final Judgment Amount', 'judgment_amount', 'decimal');

-- ============================================================================
-- BURLINGTON COUNTY (ID: 3) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(3, 'Burlington', 'SheriffNumber', 'sheriff_number', 'varchar'),
(3, 'Burlington', 'Sheriff #', 'sheriff_number', 'varchar'),
(3, 'Burlington', 'Sales Date', 'sale_date', 'date'),
(3, 'Burlington', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(3, 'Burlington', 'Plaintiff', 'plaintiff', 'varchar'),
(3, 'Burlington', 'DefendantTitle', 'defendant', 'varchar'),
(3, 'Burlington', 'Defendant', 'defendant', 'varchar'),
(3, 'Burlington', 'Address', 'property_address', 'varchar'),
(3, 'Burlington', 'CityDesc', 'city', 'varchar'),

-- Burlington may use number-only Sheriff IDs
(3, 'Burlington', 'Sale ID', 'sheriff_number', 'varchar'),
(3, 'Burlington', 'Sale Number', 'sheriff_number', 'varchar');

-- ============================================================================
-- CAMDEN COUNTY (ID: 1) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(1, 'Camden', 'SheriffNumber', 'sheriff_number', 'varchar'),
(1, 'Camden', 'Sheriff #', 'sheriff_number', 'varchar'),
(1, 'Camden', 'Sales Date', 'sale_date', 'date'),
(1, 'Camden', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(1, 'Camden', 'Plaintiff', 'plaintiff', 'varchar'),
(1, 'Camden', 'DefendantTitle', 'defendant', 'varchar'),
(1, 'Camden', 'Defendant', 'defendant', 'varchar'),
(1, 'Camden', 'Address', 'property_address', 'varchar'),
(1, 'Camden', 'CityDesc', 'city', 'varchar'),

-- Camden uses FR- prefix
(1, 'Camden', 'FR Number', 'sheriff_number', 'varchar');

-- ============================================================================
-- CUMBERLAND COUNTY (ID: 6) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(6, 'Cumberland', 'SheriffNumber', 'sheriff_number', 'varchar'),
(6, 'Cumberland', 'Sheriff #', 'sheriff_number', 'varchar'),
(6, 'Cumberland', 'Sales Date', 'sale_date', 'date'),
(6, 'Cumberland', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(6, 'Cumberland', 'Plaintiff', 'plaintiff', 'varchar'),
(6, 'Cumberland', 'DefendantTitle', 'defendant', 'varchar'),
(6, 'Cumberland', 'Defendant', 'defendant', 'varchar'),
(6, 'Cumberland', 'Address', 'property_address', 'varchar'),
(6, 'Cumberland', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- ESSEX COUNTY (ID: 2) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(2, 'Essex', 'SheriffNumber', 'sheriff_number', 'varchar'),
(2, 'Essex', 'Sheriff #', 'sheriff_number', 'varchar'),
(2, 'Essex', 'Sales Date', 'sale_date', 'date'),
(2, 'Essex', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(2, 'Essex', 'Plaintiff', 'plaintiff', 'varchar'),
(2, 'Essex', 'DefendantTitle', 'defendant', 'varchar'),
(2, 'Essex', 'Defendant', 'defendant', 'varchar'),
(2, 'Essex', 'Address', 'property_address', 'varchar'),
(2, 'Essex', 'CityDesc', 'city', 'varchar'),

-- Essex County Monetary Fields - Category A: Court/Debt Amounts
(2, 'Essex', 'Final Judgment', 'judgment_amount', 'decimal'),
(2, 'Essex', 'Judgment Amount', 'judgment_amount', 'decimal'),
(2, 'Essex', 'Writ Amount', 'writ_amount', 'decimal'),
(2, 'Essex', 'Writ of Execution', 'writ_amount', 'decimal'),

-- Essex County Monetary Fields - Category B: Auction/Sale Floor Amounts
(2, 'Essex', 'Opening Bid', 'opening_bid', 'decimal'),
(2, 'Essex', 'Minimum Bid', 'opening_bid', 'decimal'),
(2, 'Essex', 'Starting Bid', 'opening_bid', 'decimal'),

-- Essex County Monetary Fields - Category C: Estimated/Approximate Amounts
(2, 'Essex', 'Approx Upset', 'approx_upset', 'decimal'),
(2, 'Essex', 'Approx. Upset', 'approx_upset', 'decimal'),
(2, 'Essex', 'Approx Upset Price', 'approx_upset', 'decimal');

-- ============================================================================
-- GLOUCESTER COUNTY (ID: 19) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(19, 'Gloucester', 'SheriffNumber', 'sheriff_number', 'varchar'),
(19, 'Gloucester', 'Sheriff #', 'sheriff_number', 'varchar'),
(19, 'Gloucester', 'Sales Date', 'sale_date', 'date'),
(19, 'Gloucester', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(19, 'Gloucester', 'Plaintiff', 'plaintiff', 'varchar'),
(19, 'Gloucester', 'DefendantTitle', 'defendant', 'varchar'),
(19, 'Gloucester', 'Defendant', 'defendant', 'varchar'),
(19, 'Gloucester', 'Address', 'property_address', 'varchar'),
(19, 'Gloucester', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- HUDSON COUNTY (ID: 10) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(10, 'Hudson', 'SheriffNumber', 'sheriff_number', 'varchar'),
(10, 'Hudson', 'Sheriff #', 'sheriff_number', 'varchar'),
(10, 'Hudson', 'Sales Date', 'sale_date', 'date'),
(10, 'Hudson', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(10, 'Hudson', 'Plaintiff', 'plaintiff', 'varchar'),
(10, 'Hudson', 'DefendantTitle', 'defendant', 'varchar'),
(10, 'Hudson', 'Defendant', 'defendant', 'varchar'),
(10, 'Hudson', 'Address', 'property_address', 'varchar'),
(10, 'Hudson', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- HUNTERDON COUNTY (ID: 32) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(32, 'Hunterdon', 'SheriffNumber', 'sheriff_number', 'varchar'),
(32, 'Hunterdon', 'Sheriff #', 'sheriff_number', 'varchar'),
(32, 'Hunterdon', 'Sales Date', 'sale_date', 'date'),
(32, 'Hunterdon', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(32, 'Hunterdon', 'Plaintiff', 'plaintiff', 'varchar'),
(32, 'Hunterdon', 'DefendantTitle', 'defendant', 'varchar'),
(32, 'Hunterdon', 'Defendant', 'defendant', 'varchar'),
(32, 'Hunterdon', 'Address', 'property_address', 'varchar'),
(32, 'Hunterdon', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- MONMOUTH COUNTY (ID: 8) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(8, 'Monmouth', 'SheriffNumber', 'sheriff_number', 'varchar'),
(8, 'Monmouth', 'Sheriff #', 'sheriff_number', 'varchar'),
(8, 'Monmouth', 'Sales Date', 'sale_date', 'date'),
(8, 'Monmouth', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(8, 'Monmouth', 'Plaintiff', 'plaintiff', 'varchar'),
(8, 'Monmouth', 'DefendantTitle', 'defendant', 'varchar'),
(8, 'Monmouth', 'Defendant', 'defendant', 'varchar'),
(8, 'Monmouth', 'Address', 'property_address', 'varchar'),
(8, 'Monmouth', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- MORRIS COUNTY (ID: 9) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(9, 'Morris', 'SheriffNumber', 'sheriff_number', 'varchar'),
(9, 'Morris', 'Sheriff #', 'sheriff_number', 'varchar'),
(9, 'Morris', 'Sales Date', 'sale_date', 'date'),
(9, 'Morris', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(9, 'Morris', 'Plaintiff', 'plaintiff', 'varchar'),
(9, 'Morris', 'DefendantTitle', 'defendant', 'varchar'),
(9, 'Morris', 'Defendant', 'defendant', 'varchar'),
(9, 'Morris', 'Address', 'property_address', 'varchar'),
(9, 'Morris', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- PASSAIC COUNTY (ID: 17) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(17, 'Passaic', 'SheriffNumber', 'sheriff_number', 'varchar'),
(17, 'Passaic', 'Sheriff #', 'sheriff_number', 'varchar'),
(17, 'Passaic', 'Sales Date', 'sale_date', 'date'),
(17, 'Passaic', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(17, 'Passaic', 'Plaintiff', 'plaintiff', 'varchar'),
(17, 'Passaic', 'DefendantTitle', 'defendant', 'varchar'),
(17, 'Passaic', 'Defendant', 'defendant', 'varchar'),
(17, 'Passaic', 'Address', 'property_address', 'varchar'),
(17, 'Passaic', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- SALEM COUNTY (ID: 20) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(20, 'Salem', 'SheriffNumber', 'sheriff_number', 'varchar'),
(20, 'Salem', 'Sheriff #', 'sheriff_number', 'varchar'),
(20, 'Salem', 'Sales Date', 'sale_date', 'date'),
(20, 'Salem', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(20, 'Salem', 'Plaintiff', 'plaintiff', 'varchar'),
(20, 'Salem', 'DefendantTitle', 'defendant', 'varchar'),
(20, 'Salem', 'Defendant', 'defendant', 'varchar'),
(20, 'Salem', 'Address', 'property_address', 'varchar'),
(20, 'Salem', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- UNION COUNTY (ID: 15) Field Mappings
-- ============================================================================
INSERT INTO county_field_mappings (county_id, county_name, source_field_name, unified_field_name, data_type) VALUES
(15, 'Union', 'SheriffNumber', 'sheriff_number', 'varchar'),
(15, 'Union', 'Sheriff #', 'sheriff_number', 'varchar'),
(15, 'Union', 'Sales Date', 'sale_date', 'date'),
(15, 'Union', 'PlaintiffTitle', 'plaintiff', 'varchar'),
(15, 'Union', 'Plaintiff', 'plaintiff', 'varchar'),
(15, 'Union', 'DefendantTitle', 'defendant', 'varchar'),
(15, 'Union', 'Defendant', 'defendant', 'varchar'),
(15, 'Union', 'Address', 'property_address', 'varchar'),
(15, 'Union', 'CityDesc', 'city', 'varchar');

-- ============================================================================
-- STATUS MAPPINGS (Normalize different status texts)
-- ============================================================================
INSERT INTO status_mappings (county_id, raw_status_text, unified_status, is_primary) VALUES
-- Common status mappings (apply to all counties)
-- Scheduled statuses
(1, 'Scheduled - Foreclosure', 'scheduled', true),
(1, 'Scheduled', 'scheduled', true),
(1, 'Open', 'scheduled', true),

-- Adjourned statuses
(1, 'Adjourned - Plaintiff', 'adjourned_plaintiff', true),
(1, 'Adjourned Plaintiff', 'adjourned_plaintiff', true),
(1, 'Adjourned - Court', 'adjourned_court', true),
(1, 'Adjourned Court', 'adjourned_court', true),
(1, 'Adjourned - Defendant', 'adjourned_defendant', true),
(1, 'Adjourned Defendant', 'adjourned_defendant', true),
(1, 'Adjourned', 'adjourned_plaintiff', false),

-- Sold/Cancelled statuses
(1, 'Sold', 'sold', true),
(1, 'Sold/Cancelled', 'sold', false),
(1, 'Sold-Cancelled', 'sold', false),
(1, 'Cancelled', 'cancelled', true),

-- Copy for all counties (you'd want to generate these programmatically)
-- In production, you'd run a query to copy these for all county_ids
-- For brevity, showing just a few examples
(73, 'Scheduled - Foreclosure', 'scheduled', true),
(73, 'Adjourned - Plaintiff', 'adjourned_plaintiff', true),
(73, 'Adjourned - Court', 'adjourned_court', true),
(73, 'Adjourned - Defendant', 'adjourned_defendant', true),
(73, 'Sold', 'sold', true),
(73, 'Sold/Cancelled', 'sold', false);
