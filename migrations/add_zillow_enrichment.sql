-- Migration: Add Zillow enrichment columns to foreclosure_listings table
-- This adds support for storing Zillow property data from RapidAPI enrichment

-- Automatic enrichment columns (fetched immediately for all properties)
ALTER TABLE foreclosure_listings
  ADD COLUMN IF NOT EXISTS zillow_zpid bigint,
  ADD COLUMN IF NOT EXISTS zillow_zestimate numeric,
  ADD COLUMN IF NOT EXISTS zillow_bedrooms integer,
  ADD COLUMN IF NOT EXISTS zillow_bathrooms numeric,
  ADD COLUMN IF NOT EXISTS zillow_sqft integer,
  ADD COLUMN IF NOT EXISTS zillow_lot_size numeric,
  ADD COLUMN IF NOT EXISTS zillow_year_built integer,
  ADD COLUMN IF NOT EXISTS zillow_property_type varchar(50),
  ADD COLUMN IF NOT EXISTS zillow_last_sold_price numeric,
  ADD COLUMN IF NOT EXISTS zillow_last_sold_date date,
  ADD COLUMN IF NOT EXISTS zillow_comps jsonb,
  ADD COLUMN IF NOT EXISTS zillow_price_history jsonb,
  ADD COLUMN IF NOT EXISTS zillow_images jsonb,
  ADD COLUMN IF NOT EXISTS zillow_image_count integer DEFAULT 0,
  ADD COLUMN IF NOT EXISTS zillow_tax_assessment_history jsonb,
  ADD COLUMN IF NOT EXISTS zillow_tax_paid_history jsonb,
  ADD COLUMN IF NOT EXISTS zillow_annual_tax numeric,
  ADD COLUMN IF NOT EXISTS zillow_zestimate_change_percent numeric;

-- On-demand enrichment columns (fetched when user clicks "Full Details")
ALTER TABLE foreclosure_listings
  ADD COLUMN IF NOT EXISTS zillow_owner_contacts jsonb,
  ADD COLUMN IF NOT EXISTS zillow_similar_properties jsonb,
  ADD COLUMN IF NOT EXISTS zillow_nearby_properties jsonb,
  ADD COLUMN IF NOT EXISTS zillow_walk_score integer,
  ADD COLUMN IF NOT EXISTS zillow_transit_score integer,
  ADD COLUMN IF NOT EXISTS zillow_bike_score integer,
  ADD COLUMN IF NOT EXISTS zillow_climate_risk jsonb,
  ADD COLUMN IF NOT EXISTS zillow_zhvi_market jsonb,
  ADD COLUMN IF NOT EXISTS zillow_zestimate_history jsonb;

-- Metadata columns
ALTER TABLE foreclosure_listings
  ADD COLUMN IF NOT EXISTS zillow_auto_enriched_at timestamp,
  ADD COLUMN IF NOT EXISTS zillow_full_enriched_at timestamp,
  ADD COLUMN IF NOT EXISTS zillow_enrichment_status varchar(20) DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS zillow_last_error text,
  ADD COLUMN IF NOT EXISTS zillow_data jsonb;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_foreclosure_listings_zillow_zpid ON foreclosure_listings(zillow_zpid);
CREATE INDEX IF NOT EXISTS idx_foreclosure_listings_zillow_enrichment_status ON foreclosure_listings(zillow_enrichment_status);
CREATE INDEX IF NOT EXISTS idx_foreclosure_listings_zillow_auto_enriched_at ON foreclosure_listings(zillow_auto_enriched_at);
CREATE INDEX IF NOT EXISTS idx_foreclosure_listings_zestimate ON foreclosure_listings(zillow_zestimate);

-- Add comments for documentation
COMMENT ON COLUMN foreclosure_listings.zillow_zpid IS 'Zillow Property ID from RapidAPI';
COMMENT ON COLUMN foreclosure_listings.zillow_zestimate IS 'Zestimate (Zillow estimated property value)';
COMMENT ON COLUMN foreclosure_listings.zillow_comps IS 'Comparable homes data (JSON)';
COMMENT ON COLUMN foreclosure_listings.zillow_price_history IS 'Historical price data (JSON)';
COMMENT ON COLUMN foreclosure_listings.zillow_images IS 'Property images data (JSON)';
COMMENT ON COLUMN foreclosure_listings.zillow_owner_contacts IS 'Owner contact information from skip tracing (JSON)';
COMMENT ON COLUMN foreclosure_listings.zillow_enrichment_status IS 'pending, auto_enriched, fully_enriched, or failed';
COMMENT ON COLUMN foreclosure_listings.zillow_auto_enriched_at IS 'Timestamp when automatic enrichment completed';
COMMENT ON COLUMN foreclosure_listings.zillow_full_enriched_at IS 'Timestamp when on-demand enrichment completed';
