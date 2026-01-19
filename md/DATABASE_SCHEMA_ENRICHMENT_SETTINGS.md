# Database Schema - Enrichment Settings System

**Version:** 1.0
**Date:** December 27, 2025

---

## Overview

Three-tier settings system:
1. **Admin Settings** - Global defaults and locks
2. **County Settings** - Per-county overrides (admin-controlled)
3. **User Preferences** - Per-user overrides (if allowed by admin)

---

## Table 1: Admin Settings (Global Defaults)

```sql
CREATE TABLE enrichment_admin_settings (
    id SERIAL PRIMARY KEY,

    -- ============================================
    -- ZILLOW ENDPOINT DEFAULTS
    -- ============================================

    -- Core endpoints
    endpoint_pro_byaddress BOOLEAN DEFAULT true,
    endpoint_lock_pro_byaddress BOOLEAN DEFAULT false,

    endpoint_custom_ad_byzpid BOOLEAN DEFAULT true,
    endpoint_lock_custom_ad_byzpid BOOLEAN DEFAULT false,

    -- Comps
    endpoint_similar BOOLEAN DEFAULT true,
    endpoint_lock_similar BOOLEAN DEFAULT false,

    endpoint_nearby BOOLEAN DEFAULT false,
    endpoint_lock_nearby BOOLEAN DEFAULT false,

    -- History
    endpoint_pricehistory BOOLEAN DEFAULT true,
    endpoint_lock_pricehistory BOOLEAN DEFAULT false,

    endpoint_graph_listing_price BOOLEAN DEFAULT false,
    endpoint_lock_graph_listing_price BOOLEAN DEFAULT false,

    -- Financial
    endpoint_taxinfo BOOLEAN DEFAULT true,
    endpoint_lock_taxinfo BOOLEAN DEFAULT false,

    -- Location
    endpoint_climate BOOLEAN DEFAULT true,
    endpoint_lock_climate BOOLEAN DEFAULT false,

    endpoint_walk_transit_bike BOOLEAN DEFAULT true,
    endpoint_lock_walk_transit_bike BOOLEAN DEFAULT false,

    -- Market
    endpoint_housing_market BOOLEAN DEFAULT false,
    endpoint_lock_housing_market BOOLEAN DEFAULT false,

    endpoint_rental_market BOOLEAN DEFAULT false,
    endpoint_lock_rental_market BOOLEAN DEFAULT false,

    -- Contact
    endpoint_ownerinfo BOOLEAN DEFAULT false,
    endpoint_lock_ownerinfo BOOLEAN DEFAULT false,

    -- Search
    endpoint_custom_ae_search BOOLEAN DEFAULT false,
    endpoint_lock_custom_ae_search BOOLEAN DEFAULT false,

    -- ============================================
    -- EXTERNAL SKIP TRACING
    -- ============================================
    enable_skip_trace_external BOOLEAN DEFAULT true,
    skip_trace_external_enabled BOOLEAN DEFAULT false,
    skip_trace_external_lock BOOLEAN DEFAULT false,

    -- ============================================
    -- INVESTMENT CALCULATION PARAMETERS
    -- ============================================
    inv_annual_appreciation DECIMAL(5,4) DEFAULT 0.03,
    inv_mortgage_rate DECIMAL(5,4) DEFAULT 0.045,
    inv_down_payment_rate DECIMAL(5,4) DEFAULT 0.20,
    inv_insurance_rate DECIMAL(5,4) DEFAULT 0.015,
    inv_loan_term_months INTEGER DEFAULT 360,
    inv_maintenance_rate DECIMAL(5,4) DEFAULT 0.10,
    inv_property_mgmt_rate DECIMAL(5,4) DEFAULT 0.10,
    inv_property_tax_rate DECIMAL(5,4) DEFAULT 0.012,
    inv_vacancy_rate DECIMAL(5,4) DEFAULT 0.05,
    inv_renovation_cost INTEGER DEFAULT 25000,

    -- ============================================
    -- USER PERMISSIONS
    -- ============================================
    allow_user_overrides BOOLEAN DEFAULT true,
    allow_user_templates BOOLEAN DEFAULT true,
    allow_custom_investment_params BOOLEAN DEFAULT true,

    -- ============================================
    -- TIMESTAMPS
    -- ============================================
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for settings lookups
CREATE INDEX idx_admin_settings_updated ON enrichment_admin_settings(updated_at);
```

---

## Table 2: County Settings (Per-County Overrides)

```sql
CREATE TABLE county_enrichment_settings (
    id SERIAL PRIMARY KEY,

    -- ============================================
    -- COUNTY IDENTIFIER
    -- ============================================
    county_id INTEGER NOT NULL,
    county_name VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,

    -- ============================================
    -- ENDPOINT OVERRIDES (NULL = use admin default)
    -- ============================================
    endpoint_pro_byaddress BOOLEAN,
    endpoint_custom_ad_byzpid BOOLEAN,
    endpoint_similar BOOLEAN,
    endpoint_nearby BOOLEAN,
    endpoint_pricehistory BOOLEAN,
    endpoint_graph_listing_price BOOLEAN,
    endpoint_taxinfo BOOLEAN,
    endpoint_climate BOOLEAN,
    endpoint_walk_transit_bike BOOLEAN,
    endpoint_housing_market BOOLEAN,
    endpoint_rental_market BOOLEAN,
    endpoint_ownerinfo BOOLEAN,
    endpoint_custom_ae_search BOOLEAN,

    -- ============================================
    -- EXTERNAL SKIP TRACING OVERRIDE
    -- ============================================
    skip_trace_external_enabled BOOLEAN,

    -- ============================================
    -- INVESTMENT PARAMETER OVERRIDES
    -- ============================================
    inv_annual_appreciation DECIMAL(5,4),
    inv_mortgage_rate DECIMAL(5,4),
    inv_down_payment_rate DECIMAL(5,4),
    inv_insurance_rate DECIMAL(5,4),
    inv_loan_term_months INTEGER,
    inv_maintenance_rate DECIMAL(5,4),
    inv_property_mgmt_rate DECIMAL(5,4),
    inv_property_tax_rate DECIMAL(5,4),
    inv_vacancy_rate DECIMAL(5,4),
    inv_renovation_cost INTEGER,

    -- ============================================
    -- TEMPLATE PRESET
    -- ============================================
    template_preset VARCHAR(50),

    -- ============================================
    -- TIMESTAMPS
    -- ============================================
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    UNIQUE(county_id, state)
);

-- Create index for county lookups
CREATE INDEX idx_county_settings_county ON county_enrichment_settings(county_id, state);
CREATE INDEX idx_county_settings_state ON county_enrichment_settings(state);
CREATE INDEX idx_county_settings_template ON county_enrichment_settings(template_preset);
```

---

## Table 3: User Preferences (Per-User Overrides)

```sql
CREATE TABLE user_enrichment_preferences (
    id SERIAL PRIMARY KEY,

    -- ============================================
    -- USER IDENTIFIER
    -- ============================================
    user_id UUID NOT NULL,

    -- ============================================
    -- COUNTY CONTEXT
    -- ============================================
    county_id INTEGER NOT NULL,
    state VARCHAR(2) NOT NULL,

    -- ============================================
    -- ENDPOINT OVERRIDES
    -- ============================================
    endpoint_pro_byaddress BOOLEAN,
    endpoint_custom_ad_byzpid BOOLEAN,
    endpoint_similar BOOLEAN,
    endpoint_nearby BOOLEAN,
    endpoint_pricehistory BOOLEAN,
    endpoint_graph_listing_price BOOLEAN,
    endpoint_taxinfo BOOLEAN,
    endpoint_climate BOOLEAN,
    endpoint_walk_transit_bike BOOLEAN,
    endpoint_housing_market BOOLEAN,
    endpoint_rental_market BOOLEAN,
    endpoint_ownerinfo BOOLEAN,
    endpoint_custom_ae_search BOOLEAN,

    -- ============================================
    -- EXTERNAL SKIP TRACING
    -- ============================================
    skip_trace_external_enabled BOOLEAN,

    -- ============================================
    -- INVESTMENT PARAMETER OVERRIDES
    -- ============================================
    inv_annual_appreciation DECIMAL(5,4),
    inv_mortgage_rate DECIMAL(5,4),
    inv_down_payment_rate DECIMAL(5,4),
    inv_insurance_rate DECIMAL(5,4),
    inv_loan_term_months INTEGER,
    inv_maintenance_rate DECIMAL(5,4),
    inv_property_mgmt_rate DECIMAL(5,4),
    inv_property_tax_rate DECIMAL(5,4),
    inv_vacancy_rate DECIMAL(5,4),
    inv_renovation_cost INTEGER,

    -- ============================================
    -- TEMPLATE PRESET
    -- ============================================
    template_preset VARCHAR(50),

    -- ============================================
    -- TIMESTAMPS
    -- ============================================
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- ============================================
    -- CONSTRAINTS
    -- ============================================
    UNIQUE(user_id, county_id, state)
);

-- Create index for user lookups
CREATE INDEX idx_user_prefs_user ON user_enrichment_preferences(user_id);
CREATE INDEX idx_user_prefs_county ON user_enrichment_preferences(county_id, state);
CREATE INDEX idx_user_prefs_template ON user_enrichment_preferences(template_preset);
```

---

## Indexes Summary

| Table | Index | Purpose |
|-------|-------|---------|
| `enrichment_admin_settings` | `idx_admin_settings_updated` | Track settings changes |
| `county_enrichment_settings` | `idx_county_settings_county` | County lookups by ID |
| `county_enrichment_settings` | `idx_county_settings_state` | State-wide queries |
| `county_enrichment_settings` | `idx_county_settings_template` | Template queries |
| `user_enrichment_preferences` | `idx_user_prefs_user` | User lookups |
| `user_enrichment_preferences` | `idx_user_prefs_county` | User + county queries |
| `user_enrichment_preferences` | `idx_user_prefs_template` | User template queries |

---

## Migration File

**File:** `migrations/add_enrichment_settings.sql`

```sql
-- ============================================================
-- ENRICHMENT SETTINGS SYSTEM
-- ============================================================
-- Run: psql -U postgres -d your_database -f migrations/add_enrichment_settings.sql

-- 1. Create admin settings table
CREATE TABLE enrichment_admin_settings (
    -- [See full schema above]
);

-- 2. Create county settings table
CREATE TABLE county_enrichment_settings (
    -- [See full schema above]
);

-- 3. Create user preferences table
CREATE TABLE user_enrichment_preferences (
    -- [See full schema above]
);

-- 4. Insert default admin settings
INSERT INTO enrichment_admin_settings (
    endpoint_pro_byaddress, endpoint_lock_pro_byaddress,
    endpoint_custom_ad_byzpid, endpoint_lock_custom_ad_byzpid,
    endpoint_similar, endpoint_lock_similar,
    endpoint_pricehistory, endpoint_lock_pricehistory,
    endpoint_taxinfo, endpoint_lock_taxinfo,
    endpoint_climate, endpoint_lock_climate,
    endpoint_walk_transit_bike, endpoint_lock_walk_transit_bike,
    inv_annual_appreciation, inv_mortgage_rate, inv_down_payment_rate
) VALUES (
    true, true,
    true, true,
    true, true,
    true, true,
    true, true,
    true, false,
    true, false,
    0.03, 0.045, 0.20
);

-- 5. Create indexes
CREATE INDEX idx_admin_settings_updated ON enrichment_admin_settings(updated_at);
CREATE INDEX idx_county_settings_county ON county_enrichment_settings(county_id, state);
CREATE INDEX idx_county_settings_state ON county_enrichment_settings(state);
CREATE INDEX idx_user_prefs_user ON user_enrichment_preferences(user_id);
CREATE INDEX idx_user_prefs_county ON user_enrichment_preferences(county_id, state);

-- 6. Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
END;
$$ language 'plpgsql';

CREATE TRIGGER update_admin_settings_updated_at BEFORE UPDATE
    ON enrichment_admin_settings FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_county_settings_updated_at BEFORE UPDATE
    ON county_enrichment_settings FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE
    ON user_enrichment_preferences FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Rollback

```sql
-- Drop tables (order matters due to foreign keys)
DROP TABLE IF EXISTS user_enrichment_preferences;
DROP TABLE IF EXISTS county_enrichment_settings;
DROP TABLE IF EXISTS enrichment_admin_settings;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column;
```
