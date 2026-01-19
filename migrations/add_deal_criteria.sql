-- =============================================================================
-- Deal Criteria Migration for V1 MVP
-- =============================================================================
-- Migration: add_deal_criteria
-- Description: Adds user_deal_criteria table for auto-matching properties
--           based on investor criteria (price, ARV, location, etc.)
-- =============================================================================

-- =============================================================================
-- Table: user_deal_criteria
-- Purpose: User-defined criteria for automatic property matching
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_deal_criteria (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,

    -- Price Criteria
    min_upset_price DECIMAL(12,2),
    max_upset_price DECIMAL(12,2),

    -- ARV & Profit Criteria
    min_arv_percentage DECIMAL(5,2) DEFAULT 70.00,
    minimum_profit_margin DECIMAL(5,2) DEFAULT 30.00,
    max_rehab_budget DECIMAL(12,2),
    max_rehab_percentage DECIMAL(5,2) DEFAULT 30.00,

    -- Property Preferences
    preferred_property_types TEXT[] DEFAULT '{"Single Family","Multi-Family","Townhouse"}',
    preferred_counties INT[],
    preferred_cities TEXT[],
    exclude_areas TEXT[],

    -- Time Criteria
    ideal_days_to_auction INT DEFAULT 7,

    -- Risk Filters
    avoid_pending_litigation BOOLEAN DEFAULT true,
    min_data_quality_score DECIMAL(4,3) DEFAULT 0.500,

    -- Strategy Alignment
    investment_strategy TEXT,

    -- Custom Weights (JSONB for flexibility)
    custom_weights JSONB DEFAULT '{
        "price_weight": 0.25,
        "arv_weight": 0.25,
        "location_weight": 0.20,
        "condition_weight": 0.15,
        "time_weight": 0.15
    }',

    -- Matching Settings
    is_active BOOLEAN DEFAULT true,
    enable_alerts BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_deal_criteria_user_id ON user_deal_criteria(user_id);
CREATE INDEX idx_user_deal_criteria_is_active ON user_deal_criteria(user_id, is_active);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_user_deal_criteria_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_deal_criteria_updated_at
    BEFORE UPDATE ON user_deal_criteria
    FOR EACH ROW
    EXECUTE FUNCTION update_user_deal_criteria_updated_at();

-- =============================================================================
-- Table: property_match_scores
-- Purpose: Store match scores for properties against user criteria
-- =============================================================================
CREATE TABLE IF NOT EXISTS property_match_scores (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    criteria_id INT REFERENCES user_deal_criteria(id) ON DELETE CASCADE,

    -- Match Results
    match_score DECIMAL(5,4),
    match_category TEXT,  -- 'hot', 'warm', 'cold'

    -- Score Breakdown (JSONB)
    score_breakdown JSONB DEFAULT '{
        "price_score": 0,
        "arv_score": 0,
        "location_score": 0,
        "condition_score": 0,
        "time_score": 0
    }',

    -- Reasoning
    match_reasons TEXT[],
    disqualification_reasons TEXT[],

    -- Property Snapshot (for fast queries)
    property_snapshot JSONB,

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT property_match_unique UNIQUE (user_id, property_id)
);

-- Indexes
CREATE INDEX idx_property_match_scores_user_id ON property_match_scores(user_id, calculated_at DESC);
CREATE INDEX idx_property_match_scores_property_id ON property_match_scores(property_id);
CREATE INDEX idx_property_match_scores_score ON property_match_scores(user_id, match_score DESC);
CREATE INDEX idx_property_match_scores_category ON property_match_scores(user_id, match_category);

-- =============================================================================
-- Table: deal_match_alerts
-- Purpose: Track alerts sent for matching properties
-- =============================================================================
CREATE TABLE IF NOT EXISTS deal_match_alerts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
    match_id INT REFERENCES property_match_scores(id) ON DELETE CASCADE,

    -- Alert Details
    match_score DECIMAL(5,4),
    match_category TEXT,

    -- Delivery Status
    alert_type TEXT DEFAULT 'deal_match',
    delivered_via_push BOOLEAN DEFAULT false,
    delivered_via_email BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,

    -- User Interaction
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_deal_match_alerts_user_id ON deal_match_alerts(user_id, created_at DESC);
CREATE INDEX idx_deal_match_alerts_is_read ON deal_match_alerts(user_id, is_read);
CREATE INDEX idx_deal_match_alerts_property_id ON deal_match_alerts(property_id);

-- =============================================================================
-- Comments
-- =============================================================================
COMMENT ON TABLE user_deal_criteria IS 'User-defined criteria for automatic property matching';
COMMENT ON TABLE property_match_scores IS 'Calculated match scores for properties against user criteria';
COMMENT ON TABLE deal_match_alerts IS 'Alerts sent for matching properties';

-- =============================================================================
-- Migration Complete
-- =============================================================================
