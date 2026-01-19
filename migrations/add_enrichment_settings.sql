-- =============================================================================
-- Zillow Enrichment Settings & Deal Intelligence Database Migration
-- Version: 1.0
-- Date: December 27, 2025
--
-- This migration creates:
-- 1. Three-tier enrichment settings system (admin, county, user)
-- 2. Deal intelligence tables for learning-to-rank system
-- =============================================================================

-- =============================================================================
-- PART 1: ENRICHMENT SETTINGS TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: enrichment_admin_settings
-- Description: Global defaults for all enrichment endpoints (singleton table)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrichment_admin_settings (
    id SERIAL PRIMARY KEY,
    -- Always one row with id=1

    -- Endpoint Enable/Disable Flags (13 Zillow endpoints)
    endpoint_pro_byaddress BOOLEAN DEFAULT true,
    endpoint_custom_ad_byzpid BOOLEAN DEFAULT true,
    endpoint_similar BOOLEAN DEFAULT true,
    endpoint_nearby BOOLEAN DEFAULT false,
    endpoint_pricehistory BOOLEAN DEFAULT true,
    endpoint_graph_listing_price BOOLEAN DEFAULT false,
    endpoint_taxinfo BOOLEAN DEFAULT false,
    endpoint_climate BOOLEAN DEFAULT false,
    endpoint_walk_transit_bike BOOLEAN DEFAULT false,
    endpoint_housing_market BOOLEAN DEFAULT false,
    endpoint_rental_market BOOLEAN DEFAULT false,
    endpoint_ownerinfo BOOLEAN DEFAULT false,
    endpoint_custom_ae_searchbyaddress BOOLEAN DEFAULT false,

    -- Endpoint Lock Flags (prevent overrides at county/user level)
    endpoint_lock_pro_byaddress BOOLEAN DEFAULT false,
    endpoint_lock_custom_ad_byzpid BOOLEAN DEFAULT false,
    endpoint_lock_similar BOOLEAN DEFAULT false,
    endpoint_lock_nearby BOOLEAN DEFAULT false,
    endpoint_lock_pricehistory BOOLEAN DEFAULT false,
    endpoint_lock_graph_listing_price BOOLEAN DEFAULT false,
    endpoint_lock_taxinfo BOOLEAN DEFAULT false,
    endpoint_lock_climate BOOLEAN DEFAULT false,
    endpoint_lock_walk_transit_bike BOOLEAN DEFAULT false,
    endpoint_lock_housing_market BOOLEAN DEFAULT false,
    endpoint_lock_rental_market BOOLEAN DEFAULT false,
    endpoint_lock_ownerinfo BOOLEAN DEFAULT false,
    endpoint_lock_custom_ae_searchbyaddress BOOLEAN DEFAULT false,

    -- External Skip Tracing Settings
    skip_trace_external_enabled BOOLEAN DEFAULT false,
    skip_trace_external_lock BOOLEAN DEFAULT false,

    -- Investment Parameter Defaults
    inv_annual_appreciation DECIMAL(5,4) DEFAULT 0.0300,        -- 3% annual appreciation
    inv_mortgage_rate DECIMAL(5,4) DEFAULT 0.0650,            -- 6.5% mortgage rate
    inv_down_payment_rate DECIMAL(5,4) DEFAULT 0.2000,         -- 20% down payment
    inv_loan_term_months INT DEFAULT 360,                     -- 30 years
    inv_insurance_rate DECIMAL(5,4) DEFAULT 0.0150,           -- 1.5% annual insurance
    inv_property_tax_rate DECIMAL(5,4) DEFAULT 0.0120,        -- 1.2% annual property tax
    inv_maintenance_rate DECIMAL(5,4) DEFAULT 0.0100,         -- 1% annual maintenance
    inv_property_mgmt_rate DECIMAL(5,4) DEFAULT 0.0800,       -- 8% property management
    inv_vacancy_rate DECIMAL(5,4) DEFAULT 0.0500,            -- 5% vacancy
    inv_closing_costs_rate DECIMAL(5,4) DEFAULT 0.0300,       -- 3% closing costs
    inv_target_profit_margin DECIMAL(5,4) DEFAULT 0.3000,     -- 30% target profit (for MAO)
    inv_renovation_cost_default DECIMAL(12,2) DEFAULT 25000, -- Default renovation cost

    -- Permission Flags
    allow_user_overrides BOOLEAN DEFAULT true,               -- Can users set preferences?
    allow_user_templates BOOLEAN DEFAULT true,               -- Can users select templates?
    allow_custom_investment_params BOOLEAN DEFAULT false,    -- Can users customize ROI formulas?

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure only one row exists
    CONSTRAINT admin_settings_singleton CHECK (id = 1)
);

-- Insert default admin settings row
INSERT INTO enrichment_admin_settings (
    id,
    endpoint_pro_byaddress,
    endpoint_custom_ad_byzpid,
    endpoint_similar,
    endpoint_pricehistory,
    skip_trace_external_enabled
) VALUES (
    1,
    true,
    true,
    true,
    true,
    false
)
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Table: county_enrichment_settings
-- Description: Per-county enrichment settings and overrides
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS county_enrichment_settings (
    id SERIAL PRIMARY KEY,
    county_id INT NOT NULL,
    county_name VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,

    -- Endpoint Overrides (NULL = use admin default)
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
    endpoint_custom_ae_searchbyaddress BOOLEAN,

    -- Lock Flags at County Level (prevent user overrides)
    endpoint_lock_pro_byaddress BOOLEAN DEFAULT false,
    endpoint_lock_custom_ad_byzpid BOOLEAN DEFAULT false,
    endpoint_lock_similar BOOLEAN DEFAULT false,
    endpoint_lock_nearby BOOLEAN DEFAULT false,
    endpoint_lock_pricehistory BOOLEAN DEFAULT false,
    endpoint_lock_graph_listing_price BOOLEAN DEFAULT false,
    endpoint_lock_taxinfo BOOLEAN DEFAULT false,
    endpoint_lock_climate BOOLEAN DEFAULT false,
    endpoint_lock_walk_transit_bike BOOLEAN DEFAULT false,
    endpoint_lock_housing_market BOOLEAN DEFAULT false,
    endpoint_lock_rental_market BOOLEAN DEFAULT false,
    endpoint_lock_ownerinfo BOOLEAN DEFAULT false,
    endpoint_lock_custom_ae_searchbyaddress BOOLEAN DEFAULT false,

    -- Skip Tracing Override
    skip_trace_external_enabled BOOLEAN,
    skip_trace_external_lock BOOLEAN DEFAULT false,

    -- Investment Parameter Overrides (NULL = use admin default)
    inv_annual_appreciation DECIMAL(5,4),
    inv_mortgage_rate DECIMAL(5,4),
    inv_down_payment_rate DECIMAL(5,4),
    inv_loan_term_months INT,
    inv_insurance_rate DECIMAL(5,4),
    inv_property_tax_rate DECIMAL(5,4),
    inv_maintenance_rate DECIMAL(5,4),
    inv_property_mgmt_rate DECIMAL(5,4),
    inv_vacancy_rate DECIMAL(5,4),
    inv_closing_costs_rate DECIMAL(5,4),
    inv_target_profit_margin DECIMAL(5,4),
    inv_renovation_cost_default DECIMAL(12,2),

    -- Template Preset
    template_preset VARCHAR(50),
    CONSTRAINT template_preset_check
        CHECK (template_preset IN ('minimal', 'standard', 'flipper', 'landlord', 'thorough')),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one row per county
    UNIQUE(county_id, state)
);

-- Index for county lookups
CREATE INDEX idx_county_settings_county_id ON county_enrichment_settings(county_id);
CREATE INDEX idx_county_settings_state ON county_enrichment_settings(state);
CREATE INDEX idx_county_settings_template ON county_enrichment_settings(template_preset);

-- -----------------------------------------------------------------------------
-- Table: user_enrichment_preferences
-- Description: Per-user enrichment preferences (if allowed by admin)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_enrichment_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    county_id INT NOT NULL,
    state VARCHAR(2) NOT NULL,

    -- Endpoint Overrides (NULL = use county/admin default)
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
    endpoint_custom_ae_searchbyaddress BOOLEAN,

    -- Skip Tracing Override
    skip_trace_external_enabled BOOLEAN,

    -- Investment Parameter Overrides (NULL = use county/admin default)
    inv_annual_appreciation DECIMAL(5,4),
    inv_mortgage_rate DECIMAL(5,4),
    inv_down_payment_rate DECIMAL(5,4),
    inv_loan_term_months INT,
    inv_insurance_rate DECIMAL(5,4),
    inv_property_tax_rate DECIMAL(5,4),
    inv_maintenance_rate DECIMAL(5,4),
    inv_property_mgmt_rate DECIMAL(5,4),
    inv_vacancy_rate DECIMAL(5,4),
    inv_closing_costs_rate DECIMAL(5,4),
    inv_target_profit_margin DECIMAL(5,4),
    inv_renovation_cost_default DECIMAL(12,2),

    -- Template Preset Override
    template_preset VARCHAR(50),
    CONSTRAINT user_template_preset_check
        CHECK (template_preset IN ('minimal', 'standard', 'flipper', 'landlord', 'thorough')),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one row per user per county
    UNIQUE(user_id, county_id, state)
);

-- Indexes for user lookups
CREATE INDEX idx_user_prefs_user_id ON user_enrichment_preferences(user_id);
CREATE INDEX idx_user_prefs_county ON user_enrichment_preferences(county_id);


-- =============================================================================
-- PART 2: DEAL INTELLIGENCE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_investor_criteria
-- Description: Custom investor criteria for deal ranking
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_investor_criteria (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    criteria_name VARCHAR(100),

    -- Location Preferences
    preferred_counties INT[] DEFAULT '{}',
    excluded_counties INT[] DEFAULT '{}',

    -- Property Preferences
    property_types VARCHAR(50)[] DEFAULT '{}',
    CONSTRAINT property_types_check
        CHECK (property_types <@ ARRAY['residential', 'commercial', 'vacant_land', 'multi_family', 'townhouse', 'condo']::VARCHAR(50)[]),

    -- Price Range
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    CONSTRAINT price_range_check CHECK (min_price IS NULL OR max_price IS NULL OR min_price < max_price),

    -- Size Preferences
    min_sqft INT,
    max_sqft INT,
    CONSTRAINT sqft_range_check CHECK (min_sqft IS NULL OR max_sqft IS NULL OR min_sqft <= max_sqft),

    -- Bedroom/Bathroom Preferences
    min_bedrooms INT,
    max_bedrooms INT,
    CONSTRAINT bedroom_range_check CHECK (min_bedrooms IS NULL OR max_bedrooms IS NULL OR min_bedrooms <= max_bedrooms),

    min_bathrooms DECIMAL(3,1),
    max_bathrooms DECIMAL(3,1),
    CONSTRAINT bathroom_range_check CHECK (min_bathrooms IS NULL OR max_bathrooms IS NULL OR min_bathrooms <= max_bathrooms),

    -- Age Preference (max_year_built = newest acceptable)
    max_year_built INT,

    -- Investment Criteria
    min_arv_spread DECIMAL(5,2),           -- Minimum ARV/purchase ratio (e.g., 0.30 = 30%)
    max_climate_score INT,                 -- 1-10 risk score (lower is better)

    -- Location Requirements
    require_walk_score BOOLEAN DEFAULT false,
    min_walk_score INT CHECK (min_walk_score BETWEEN 0 AND 100),

    -- Risk Tolerance
    risk_tolerance VARCHAR(20) DEFAULT 'moderate',
    CONSTRAINT risk_tolerance_check
        CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),

    -- Feature Weights (for scoring customization)
    weight_arv_spread DECIMAL(3,2) DEFAULT 1.0,
    weight_cash_flow DECIMAL(3,2) DEFAULT 1.0,
    weight_location DECIMAL(3,2) DEFAULT 0.5,
    weight_condition DECIMAL(3,2) DEFAULT 0.5,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: criteria names per user
    UNIQUE(user_id, criteria_name)
);

-- Indexes
CREATE INDEX idx_investor_criteria_user_id ON deal_intelligence_investor_criteria(user_id);
CREATE INDEX idx_investor_criteria_active ON deal_intelligence_investor_criteria(user_id, is_active);

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_attention_scores
-- Description: Computed attention scores for properties per user
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_attention_scores (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    user_id UUID NOT NULL,

    -- Score (0-100)
    score DECIMAL(6,3) NOT NULL CHECK (score BETWEEN 0 AND 100),

    -- Ranking Position
    rank_position INT,
    total_properties INT,

    -- Criteria Snapshot (what settings were used)
    criteria_used JSONB DEFAULT '{}',

    -- Feature Contributions (breakdown of score)
    feature_contributions JSONB DEFAULT '{}',

    -- Risk Flags
    risk_flags JSONB DEFAULT '{}',

    -- Explanations (human-readable)
    explanations JSONB DEFAULT '{}',

    -- Model Uncertainty (0-1, higher = more uncertain)
    uncertainty DECIMAL(5,3) CHECK (uncertainty BETWEEN 0 AND 1),

    -- Model Info
    model_version VARCHAR(50) DEFAULT 'rules_v1',

    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one score per property per user
    UNIQUE(property_id, user_id),

    -- Foreign Key to foreclosure_listings (if table exists)
    CONSTRAINT fk_attention_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_attention_scores_property ON deal_intelligence_attention_scores(property_id);
CREATE INDEX idx_attention_scores_user ON deal_intelligence_attention_scores(user_id);
CREATE INDEX idx_attention_scores_rank ON deal_intelligence_attention_scores(user_id, rank_position);
CREATE INDEX idx_attention_scores_computed ON deal_intelligence_attention_scores(computed_at DESC);

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_feedback
-- Description: Investor actions for learning (keep, pass, bid, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_feedback (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    user_id UUID NOT NULL,

    -- Feedback Type
    feedback_type VARCHAR(20) NOT NULL,
    CONSTRAINT feedback_type_check
        CHECK (feedback_type IN ('keep', 'pass', 'bid', 'watch', 'ignore')),

    -- Bid Information (if applicable)
    bid_amount DECIMAL(12,2),
    bid_won BOOLEAN,
    actual_purchase_price DECIMAL(12,2),

    -- Engagement Metrics
    time_spent_seconds INT,                 -- How long user viewed property
    view_count INT DEFAULT 1,               -- Number of times viewed

    -- User Annotations
    notes TEXT,
    tags VARCHAR(50)[],
    satisfaction_rating INT CHECK (satisfaction_rating BETWEEN 1 AND 5),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key
    CONSTRAINT fk_feedback_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_feedback_property_user ON deal_intelligence_feedback(property_id, user_id);
CREATE INDEX idx_feedback_type ON deal_intelligence_feedback(feedback_type);
CREATE INDEX idx_feedback_user ON deal_intelligence_feedback(user_id);
CREATE INDEX idx_feedback_created ON deal_intelligence_feedback(created_at DESC);
CREATE INDEX idx_feedback_keep_pass ON deal_intelligence_feedback(user_id, feedback_type)
    WHERE feedback_type IN ('keep', 'pass', 'bid');

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_model_weights
-- Description: Trained model parameters per user
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_model_weights (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,

    -- Model Type
    model_type VARCHAR(50) DEFAULT 'lambdarank',
    CONSTRAINT model_type_check
        CHECK (model_type IN ('rules', 'lambdarank', 'xgboost')),

    -- Feature Weights (JSONB for flexibility)
    feature_weights JSONB NOT NULL DEFAULT '{}',

    -- Performance Metrics
    performance_metrics JSONB DEFAULT '{}',   -- {ndcg: 0.75, precision: 0.68, recall: 0.60}

    -- Training Info
    training_samples INT DEFAULT 0,
    last_trained_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Only one active model per user
    UNIQUE(user_id, is_active)
);

-- Indexes
CREATE INDEX idx_model_weights_user ON deal_intelligence_model_weights(user_id);

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_feature_importance
-- Description: Track feature importance over time
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_feature_importance (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    feature_name VARCHAR(100) NOT NULL,

    -- Importance Score (0-100)
    importance_score DECIMAL(6,3),

    -- Trend Direction
    trend VARCHAR(20),
    CONSTRAINT trend_check
        CHECK (trend IN ('increasing', 'stable', 'decreasing')),

    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_feature_importance_user ON deal_intelligence_feature_importance(user_id);
CREATE INDEX idx_feature_importance_name ON deal_intelligence_feature_importance(user_id, feature_name);
CREATE INDEX idx_feature_importance_computed ON deal_intelligence_feature_importance(computed_at DESC);

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_exploration
-- Description: Track exploration sampling for safe discovery
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_exploration (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    user_id UUID NOT NULL,

    -- Exploration Type
    exploration_type VARCHAR(30) NOT NULL,
    CONSTRAINT exploration_type_check
        CHECK (exploration_type IN ('uncertainty_sample', 'diversity', 'novelty')),

    -- Expected Value
    expected_gain DECIMAL(6,3),

    -- Actual Outcome
    actual_outcome VARCHAR(20),
    CONSTRAINT outcome_check
        CHECK (actual_outcome IS NULL OR actual_outcome IN ('positive', 'neutral', 'negative')),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key
    CONSTRAINT fk_exploration_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_exploration_user ON deal_intelligence_exploration(user_id, created_at DESC);
CREATE INDEX idx_exploration_property ON deal_intelligence_exploration(property_id);
CREATE INDEX idx_exploration_type ON deal_intelligence_exploration(exploration_type);

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_ranking_history
-- Description: Historical rankings for analysis and model improvement
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deal_intelligence_ranking_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT NOT NULL,
    rank_position INT NOT NULL,
    score DECIMAL(6,3) NOT NULL,
    snapshot_date DATE NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key
    CONSTRAINT fk_ranking_history_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_ranking_history_snapshot ON deal_intelligence_ranking_history(user_id, snapshot_date, rank_position);
CREATE INDEX idx_ranking_history_property ON deal_intelligence_ranking_history(property_id);
CREATE INDEX idx_ranking_history_date ON deal_intelligence_ranking_history(snapshot_date DESC);


-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE enrichment_admin_settings IS 'Global enrichment settings (singleton, id=1)';
COMMENT ON TABLE county_enrichment_settings IS 'Per-county enrichment endpoint overrides';
COMMENT ON TABLE user_enrichment_preferences IS 'Per-user enrichment preferences (if allowed by admin)';

COMMENT ON TABLE deal_intelligence_investor_criteria IS 'Custom investor criteria for deal ranking';
COMMENT ON TABLE deal_intelligence_attention_scores IS 'Computed attention scores (0-100) per property per user';
COMMENT ON TABLE deal_intelligence_feedback IS 'Investor actions (keep/pass/bid) for learning';
COMMENT ON TABLE deal_intelligence_model_weights IS 'Trained LambdaRank model parameters';
COMMENT ON TABLE deal_intelligence_feature_importance IS 'Feature importance tracking over time';
COMMENT ON TABLE deal_intelligence_exploration IS 'Safe exploration sampling records';
COMMENT ON TABLE deal_intelligence_ranking_history IS 'Historical rankings for analysis';

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
-- Total tables created: 10
-- - Enrichment settings: 3 tables
-- - Deal intelligence: 7 tables
-- =============================================================================
