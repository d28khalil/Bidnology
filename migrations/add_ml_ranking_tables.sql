-- =============================================================================
-- ML-Based Property Ranking System
-- Version: 1.0
-- Date: December 28, 2025
--
-- This migration creates tables for ML-powered property ranking with:
-- - Per-user investor criteria storage
-- - Model weight tracking
-- - Feature importance analysis
-- - Human feedback loop for continuous improvement
-- - Graceful handling of incomplete Zillow data
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_investor_criteria
-- Description: Per-user investment preferences for personalized ranking
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_investor_criteria (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,

    -- Price Preferences
    min_upset_price DECIMAL(12,2),
    max_upset_price DECIMAL(12,2),

    -- Property Type Preferences
    preferred_property_types VARCHAR(50)[],
    -- e.g., '{single_family,multi_family,condo,townhouse}'

    -- Location Preferences
    preferred_counties INT[],
    preferred_cities VARCHAR(100)[],
    exclude_areas VARCHAR(100)[],  -- Areas to exclude

    -- ROI Targets
    min_arv_percentage DECIMAL(5,2),
    -- Minimum ARV as % of upset price (e.g., 150 = 150%)

    max_price_per_sqft DECIMAL(10,2),

    minimum_profit_margin DECIMAL(5,2),
    -- Minimum profit as % (e.g., 30 = 30%)

    -- Risk Tolerance
    max_rehab_budget DECIMAL(12,2),
    max_rehab_percentage DECIMAL(5,2),
    -- Max rehab as % of ARV

    -- Urgency Preferences
    ideal_days_to_auction INT,
    -- How many days before auction they like to see properties

    avoid_pending_litigation BOOLEAN DEFAULT false,

    -- Strategy Preferences
    investment_strategy VARCHAR(30),
    CONSTRAINT strategy_check
        CHECK (investment_strategy IN (
            'fix_and_flip', 'buy_and_hold', 'wholesale',
            'rental', 'multi_family', 'mixed_use', 'flexible'
        )),

    -- ML Model Personalization
    custom_weights JSONB DEFAULT '{}',
    -- User can adjust feature weights:
    -- {"price_to_value": 0.4, "anomaly": 0.25, "urgency": 0.15, ...}

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_investor_criteria_user ON deal_intelligence_investor_criteria(user_id);
CREATE INDEX IF NOT EXISTS idx_investor_criteria_counties ON deal_intelligence_investor_criteria USING GIN(preferred_counties);
CREATE INDEX IF NOT EXISTS idx_investor_criteria_active ON deal_intelligence_investor_criteria(user_id, is_active);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_model_weights
-- Description: Global ML model weights for feature scoring
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_model_weights (
    id SERIAL PRIMARY KEY,

    -- Model Version
    model_version VARCHAR(50) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,

    -- Feature Weights (sum should = 1.0)
    weights JSONB DEFAULT '{
        "price_to_value": 0.35,
        "anomaly": 0.20,
        "urgency": 0.15,
        "property_type": 0.10,
        "price_range": 0.10,
        "location_score": 0.10
    }',

    -- Scoring Parameters
    price_to_value_excellent DECIMAL(4,2) DEFAULT 0.60,  -- 60% or below = excellent
    price_to_value_good DECIMAL(4,2) DEFAULT 0.70,       -- 70% or below = good
    price_to_value_fair DECIMAL(4,2) DEFAULT 0.85,       -- 85% or below = fair

    anomaly_excellent_zscore DECIMAL(5,2) DEFAULT -2.5,  -- -2.5 or below = excellent
    anomaly_good_zscore DECIMAL(5,2) DEFAULT -2.0,
    anomaly_fair_zscore DECIMAL(5,2) DEFAULT -1.5,

    urgency_urgent_days INT DEFAULT 7,
    urgency_soon_days INT DEFAULT 14,
    urgency_normal_days INT DEFAULT 30,

    -- Training Metadata
    trained_at TIMESTAMPTZ,
    training_samples_count INT DEFAULT 0,
    accuracy_score DECIMAL(4,3),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_weights_active ON deal_intelligence_model_weights(is_active, created_at DESC);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_feature_importance
-- Description: Track which features are most predictive for users
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_feature_importance (
    id SERIAL PRIMARY KEY,

    -- Feature Name
    feature_name VARCHAR(50) NOT NULL,

    -- Importance Metrics
    global_importance DECIMAL(4,3),  -- Overall importance across all users
    average_correlation DECIMAL(4,3),  -- Correlation with positive feedback

    -- Usage Statistics
    usage_count INT DEFAULT 0,
    positive_feedback_count INT DEFAULT 0,
    negative_feedback_count INT DEFAULT 0,

    -- Data Quality
    data_availability_percent DECIMAL(5,2),
    -- What % of properties have this feature populated

    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feature_importance_name ON deal_intelligence_feature_importance(feature_name);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_feedback
-- Description: User feedback on ranking quality for continuous learning
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_feedback (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT NOT NULL,

    -- Feedback Details
    is_positive BOOLEAN NOT NULL,
    -- true = user liked this property in their ranking
    -- false = user didn't think it should be ranked high

    ranking_position_at_feedback INT,
    -- What position was this property when user gave feedback?

    -- Context
    feedback_type VARCHAR(30),
    CONSTRAINT feedback_type_check
        CHECK (feedback_type IN (
            'viewed_property', 'saved_property', 'hid_property',
            'marked_good_deal', 'marked_bad_deal', 'bid_on_property'
        )),

    -- Action Taken
    user_action VARCHAR(50),
    -- e.g., "saved_to_watchlist", "requested_comps", "visited_property"

    -- Model Version
    model_version VARCHAR(50),

    -- Property State at Feedback Time (snapshot)
    property_snapshot JSONB DEFAULT '{}',
    -- Stores relevant features at time of feedback

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_feedback_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON deal_intelligence_feedback(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_property ON deal_intelligence_feedback(property_id);
CREATE INDEX IF NOT EXISTS idx_feedback_positive ON deal_intelligence_feedback(is_positive, created_at);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_ranking_history
-- Description: Track ranking score changes over time for analytics
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_ranking_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT NOT NULL,

    -- Score Details
    score DECIMAL(5,2) NOT NULL,
    confidence DECIMAL(4,3) NOT NULL,
    -- Confidence = sum of (feature_weight * feature_data_confidence)

    -- Data Quality
    data_quality VARCHAR(20),
    CONSTRAINT data_quality_check
        CHECK (data_quality IN ('high', 'medium', 'low', 'incomplete')),

    -- Score Breakdown
    breakdown JSONB DEFAULT '{}',

    -- Missing Features
    missing_features VARCHAR(50)[],
    -- e.g., '{zestimate, comps, living_area}'

    -- Model Info
    model_version VARCHAR(50),
    model_weights_id INT,

    -- Position in User's Feed
    feed_position INT,
    properties_shown_count INT,

    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_ranking_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ranking_weights
        FOREIGN KEY (model_weights_id)
        REFERENCES deal_intelligence_model_weights(id)
);

CREATE INDEX IF NOT EXISTS idx_ranking_user_property ON deal_intelligence_ranking_history(user_id, property_id);
CREATE INDEX IF NOT EXISTS idx_ranking_user_date ON deal_intelligence_ranking_history(user_id, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_score ON deal_intelligence_ranking_history(score DESC);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_exploration
-- Description: Track user property exploration patterns for ranking improvement
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_exploration (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,

    -- Exploration Session
    session_id UUID,
    session_start_time TIMESTAMPTZ DEFAULT NOW(),

    -- Properties Viewed
    properties_viewed INT[],
    -- Array of property_ids viewed in this session

    -- Filters Applied
    filters_applied JSONB DEFAULT '{}',

    -- User Actions
    actions JSONB DEFAULT '[]',

    -- Ranking Interaction
    ranking_sort_by VARCHAR(30),
    -- How user sorted (score, price, auction_date, etc.)

    properties_expanded_count INT DEFAULT 0,
    -- How many property details user clicked to expand

    -- Session Outcome
    session_duration_seconds INT,
    properties_saved_count INT DEFAULT 0,
    properties_hidden_count INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exploration_user ON deal_intelligence_exploration(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_exploration_session ON deal_intelligence_exploration(session_id);


-- -----------------------------------------------------------------------------
-- Table: deal_intelligence_attention_scores
-- Description: Track what users actually pay attention to (implicit feedback)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_intelligence_attention_scores (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT NOT NULL,

    -- Attention Metrics
    view_count INT DEFAULT 0,
    total_view_duration_seconds INT DEFAULT 0,

    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,

    -- Engagement Actions
    saved_to_watchlist BOOLEAN DEFAULT false,
    saved_to_favorites BOOLEAN DEFAULT false,
    shared_with_team BOOLEAN DEFAULT false,
    requested_comps BOOLEAN DEFAULT false,
    marked_as_hot_deal BOOLEAN DEFAULT false,
    hid_from_feed BOOLEAN DEFAULT false,

    -- Position When Viewed
    first_seen_ranking_position INT,
    first_seen_feed_position INT,

    -- Attention Score (calculated)
    attention_score DECIMAL(5,2) DEFAULT 0,
    -- Composite score based on all engagement factors

    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, property_id),

    CONSTRAINT fk_attention_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attention_user ON deal_intelligence_attention_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_attention_score ON deal_intelligence_attention_scores(attention_score DESC);
CREATE INDEX IF NOT EXISTS idx_attention_property ON deal_intelligence_attention_scores(property_id);


-- =============================================================================
-- Insert Default Model Weights
-- =============================================================================

INSERT INTO deal_intelligence_model_weights (
    model_version,
    is_active,
    weights,
    trained_at
) VALUES (
    '1.0',
    true,
    '{
        "price_to_value": 0.35,
        "anomaly": 0.20,
        "urgency": 0.15,
        "property_type": 0.10,
        "price_range": 0.10,
        "location_score": 0.10
    }'::jsonb,
    NOW()
)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- Insert Default Feature Importance
-- =============================================================================

INSERT INTO deal_intelligence_feature_importance (
    feature_name,
    global_importance,
    data_availability_percent
) VALUES
    ('price_to_value', 0.35, 95.0),
    ('anomaly', 0.20, 60.0),
    ('urgency', 0.15, 100.0),
    ('property_type', 0.10, 85.0),
    ('price_range', 0.10, 100.0),
    ('location_score', 0.10, 100.0),
    ('comps_count', 0.0, 70.0),
    ('price_per_sqft', 0.0, 75.0)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- Create Trigger for Updated At
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_investor_criteria_updated_at
    BEFORE UPDATE ON deal_intelligence_investor_criteria
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_weights_updated_at
    BEFORE UPDATE ON deal_intelligence_model_weights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attention_scores_updated_at
    BEFORE UPDATE ON deal_intelligence_attention_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
