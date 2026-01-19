-- =============================================================================
-- Deal Intelligence Features Migration
-- =============================================================================
-- Migration: add_deal_intelligence_features
-- Description: Adds 15 tables for the enhanced deal intelligence system
-- Features: Market anomalies, comps analysis, renovation estimates, investment
--           strategies, watchlist alerts, portfolio tracking, team collaboration,
--           mobile notifications, notes/checklist, export, save, kanban
-- =============================================================================

-- =============================================================================
-- Table 1: deal_features_admin_settings
-- Purpose: Feature toggle flags and AI quality thresholds (singleton)
-- =============================================================================
CREATE TABLE IF NOT EXISTS deal_features_admin_settings (
    id SERIAL PRIMARY KEY,
    CONSTRAINT admin_features_singleton CHECK (id = 1),

    -- Feature Toggle Flags (12 features)
    feature_market_anomaly_detection BOOLEAN DEFAULT false,
    feature_comparable_sales_analysis BOOLEAN DEFAULT false,
    feature_renovation_cost_estimator BOOLEAN DEFAULT false,
    feature_investment_strategies BOOLEAN DEFAULT false,
    feature_watchlist_alerts BOOLEAN DEFAULT false,
    feature_portfolio_tracking BOOLEAN DEFAULT false,
    feature_team_collaboration BOOLEAN DEFAULT false,
    feature_mobile_notifications BOOLEAN DEFAULT false,
    feature_notes_checklist BOOLEAN DEFAULT false,
    feature_export_csv BOOLEAN DEFAULT true,
    feature_save_property BOOLEAN DEFAULT true,
    feature_kanban_board BOOLEAN DEFAULT false,

    -- Feature Lock Flags (prevent lower-level overrides)
    feature_lock_market_anomaly_detection BOOLEAN DEFAULT false,
    feature_lock_comparable_sales_analysis BOOLEAN DEFAULT false,
    feature_lock_renovation_cost_estimator BOOLEAN DEFAULT false,
    feature_lock_investment_strategies BOOLEAN DEFAULT false,
    feature_lock_watchlist_alerts BOOLEAN DEFAULT false,
    feature_lock_portfolio_tracking BOOLEAN DEFAULT false,
    feature_lock_team_collaboration BOOLEAN DEFAULT false,
    feature_lock_mobile_notifications BOOLEAN DEFAULT false,
    feature_lock_notes_checklist BOOLEAN DEFAULT false,
    feature_lock_export_csv BOOLEAN DEFAULT false,
    feature_lock_save_property BOOLEAN DEFAULT false,
    feature_lock_kanban_board BOOLEAN DEFAULT false,

    -- AI Data Quality Thresholds (Market Anomaly Detection)
    anomaly_min_comps INT DEFAULT 3,
    anomaly_min_confidence DECIMAL(4,3) DEFAULT 0.700,
    anomaly_max_zscore DECIMAL(5,2) DEFAULT 2.50,
    anomaly_min_price_diff_percent DECIMAL(5,2) DEFAULT 15.00,

    -- AI Data Quality Thresholds (Comparable Sales Analysis)
    comps_analysis_min_samples INT DEFAULT 3,
    comps_analysis_max_distance_miles DECIMAL(6,2) DEFAULT 1.0,
    comps_analysis_max_age_days INT DEFAULT 365,
    comps_analysis_min_similarity_score DECIMAL(4,3) DEFAULT 0.600,

    -- AI Data Quality Thresholds (Renovation Estimator)
    renovation_min_photos INT DEFAULT 1,
    renovation_confidence_threshold DECIMAL(4,3) DEFAULT 0.500,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure singleton row exists
INSERT INTO deal_features_admin_settings (id)
VALUES (1)
ON CONFLICT DO NOTHING;

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_deal_features_admin_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER deal_features_admin_settings_updated_at
    BEFORE UPDATE ON deal_features_admin_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 2: deal_features_county_settings
-- Purpose: County-level feature overrides
-- =============================================================================
CREATE TABLE IF NOT EXISTS deal_features_county_settings (
    id SERIAL PRIMARY KEY,
    county_id INT UNIQUE REFERENCES counties(id) ON DELETE CASCADE,

    -- Feature Override Flags (can be null to inherit from admin)
    override_market_anomaly_detection BOOLEAN,
    override_comparable_sales_analysis BOOLEAN,
    override_renovation_cost_estimator BOOLEAN,
    override_investment_strategies BOOLEAN,
    override_watchlist_alerts BOOLEAN,
    override_portfolio_tracking BOOLEAN,
    override_team_collaboration BOOLEAN,
    override_mobile_notifications BOOLEAN,
    override_notes_checklist BOOLEAN,
    override_export_csv BOOLEAN,
    override_save_property BOOLEAN,
    override_kanban_board BOOLEAN,

    -- Lock Flags (prevent user-level overrides)
    county_lock_market_anomaly_detection BOOLEAN DEFAULT false,
    county_lock_comparable_sales_analysis BOOLEAN DEFAULT false,
    county_lock_renovation_cost_estimator BOOLEAN DEFAULT false,
    county_lock_investment_strategies BOOLEAN DEFAULT false,
    county_lock_watchlist_alerts BOOLEAN DEFAULT false,
    county_lock_portfolio_tracking BOOLEAN DEFAULT false,
    county_lock_team_collaboration BOOLEAN DEFAULT false,
    county_lock_mobile_notifications BOOLEAN DEFAULT false,
    county_lock_notes_checklist BOOLEAN DEFAULT false,
    county_lock_export_csv BOOLEAN DEFAULT false,
    county_lock_save_property BOOLEAN DEFAULT false,
    county_lock_kanban_board BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER deal_features_county_settings_updated_at
    BEFORE UPDATE ON deal_features_county_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 3: deal_features_user_preferences
-- Purpose: User-level feature preferences
-- =============================================================================
CREATE TABLE IF NOT EXISTS deal_features_user_preferences (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    county_id INT REFERENCES counties(id) ON DELETE SET NULL,

    -- User Preference Flags (null = inherit from county/admin)
    pref_market_anomaly_detection BOOLEAN,
    pref_comparable_sales_analysis BOOLEAN,
    pref_renovation_cost_estimator BOOLEAN,
    pref_investment_strategies BOOLEAN,
    pref_watchlist_alerts BOOLEAN,
    pref_portfolio_tracking BOOLEAN,
    pref_team_collaboration BOOLEAN,
    pref_mobile_notifications BOOLEAN,
    pref_notes_checklist BOOLEAN,
    pref_export_csv BOOLEAN,
    pref_save_property BOOLEAN,
    pref_kanban_board BOOLEAN,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER deal_features_user_preferences_updated_at
    BEFORE UPDATE ON deal_features_user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 4: market_anomalies
-- Purpose: Store detected price anomaly analysis results
-- =============================================================================
CREATE TABLE IF NOT EXISTS market_anomalies (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Analysis Results
    is_anomaly BOOLEAN NOT NULL,
    anomaly_type TEXT,
    z_score DECIMAL(8,3),
    confidence_score DECIMAL(4,3),
    price_difference_percent DECIMAL(8,2),
    estimated_market_value DECIMAL(12,2),
    estimated_value_range_low DECIMAL(12,2),
    estimated_value_range_high DECIMAL(12,2),

    -- Comparable Properties Used
    comparable_count INT,
    comparable_avg_price DECIMAL(12,2),
    comparable_median_price DECIMAL(12,2),
    comparable_price_std_dev DECIMAL(12,2),

    -- AI Analysis
    ai_reasoning TEXT,
    ai_disclaimer TEXT,

    -- Validation
    passed_quality_checks BOOLEAN DEFAULT true,
    quality_check_warnings JSONB,

    -- Human Feedback
    is_verified BOOLEAN,
    verified_by_user_id TEXT,
    verified_at TIMESTAMPTZ,
    user_feedback TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_market_anomalies_property_id ON market_anomalies(property_id);
CREATE INDEX idx_market_anomalies_is_anomaly ON market_anomalies(is_anomaly);
CREATE INDEX idx_market_anomalies_created_at ON market_anomalies(created_at DESC);
CREATE INDEX idx_market_anomalies_confidence ON market_anomalies(confidence_score DESC);

CREATE TRIGGER market_anomalies_updated_at
    BEFORE UPDATE ON market_anomalies
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 5: comparable_sales_analysis
-- Purpose: AI-powered comparable sales analysis
-- =============================================================================
CREATE TABLE IF NOT EXISTS comparable_sales_analysis (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Subject Property
    subject_address TEXT,
    subject_city TEXT,
    subject_state TEXT,
    subject_zip TEXT,
    subject_bedrooms INT,
    subject_bathrooms INT,
    subject_square_feet INT,
    subject_lot_size INT,
    subject_year_built INT,

    -- AI Analysis Results
    ai_summary TEXT,
    ai_key_insights JSONB,
    ai_market_trends TEXT,
    ai_price_recommendation TEXT,
    estimated_value DECIMAL(12,2),
    confidence_score DECIMAL(4,3),

    -- Comps Statistics
    total_comps_found INT,
    comps_analyzed INT,
    comps_avg_price DECIMAL(12,2),
    comps_median_price DECIMAL(12,2),
    comps_price_per_sqft_avg DECIMAL(8,2),
    comps_avg_days_on_market INT,

    -- Validation
    passed_quality_checks BOOLEAN DEFAULT true,
    quality_check_warnings JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comps_analysis_property_id ON comparable_sales_analysis(property_id);
CREATE INDEX idx_comps_analysis_confidence ON comparable_sales_analysis(confidence_score DESC);

CREATE TRIGGER comparable_sales_analysis_updated_at
    BEFORE UPDATE ON comparable_sales_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 6: comparable_properties
-- Purpose: Individual comparable property data
-- =============================================================================
CREATE TABLE IF NOT EXISTS comparable_properties (
    id SERIAL PRIMARY KEY,
    analysis_id INT NOT NULL REFERENCES comparable_sales_analysis(id) ON DELETE CASCADE,

    -- Comp Property Data
    zillow_zpid TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,

    -- Property Characteristics
    bedrooms INT,
    bathrooms INT,
    square_feet INT,
    lot_size INT,
    year_built INT,
    property_type TEXT,

    -- Pricing
    list_price DECIMAL(12,2),
    price_per_sqft DECIMAL(8,2),

    -- Location Metrics
    distance_miles DECIMAL(6,2),
    similarity_score DECIMAL(4,3),

    -- Sale Data
    last_sold_date DATE,
    last_sold_price DECIMAL(12,2),
    days_on_market INT,

    -- Source
    data_source TEXT DEFAULT 'zillow',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comparable_properties_analysis_id ON comparable_properties(analysis_id);
CREATE INDEX idx_comparable_properties_distance ON comparable_properties(distance_miles);
CREATE INDEX idx_comparable_properties_similarity ON comparable_properties(similarity_score DESC);


-- =============================================================================
-- Table 7: renovation_estimates
-- Purpose: Photo-based renovation cost estimates
-- =============================================================================
CREATE TABLE IF NOT EXISTS renovation_estimates (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- AI Analysis Results
    total_estimated_cost DECIMAL(12,2),
    cost_range_low DECIMAL(12,2),
    cost_range_high DECIMAL(12,2),
    confidence_score DECIMAL(4,3),

    -- Room-by-Room Breakdown
    room_breakdown JSONB,

    -- Category Breakdown
    kitchen_cost DECIMAL(10,2) DEFAULT 0,
    bathroom_cost DECIMAL(10,2) DEFAULT 0,
    flooring_cost DECIMAL(10,2) DEFAULT 0,
    roofing_cost DECIMAL(10,2) DEFAULT 0,
    hvac_cost DECIMAL(10,2) DEFAULT 0,
    electrical_cost DECIMAL(10,2) DEFAULT 0,
    plumbing_cost DECIMAL(10,2) DEFAULT 0,
    exterior_cost DECIMAL(10,2) DEFAULT 0,
    other_cost DECIMAL(10,2) DEFAULT 0,

    -- Analysis Metadata
    photos_analyzed INT,
    ai_summary TEXT,
    ai_recommendations TEXT,
    detected_issues JSONB,

    -- Validation
    passed_quality_checks BOOLEAN DEFAULT true,
    quality_check_warnings JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_renovation_estimates_property_id ON renovation_estimates(property_id);
CREATE INDEX idx_renovation_estimates_confidence ON renovation_estimates(confidence_score DESC);

CREATE TRIGGER renovation_estimates_updated_at
    BEFORE UPDATE ON renovation_estimates
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 8: investment_strategies
-- Purpose: User-defined investment strategy templates
-- =============================================================================
CREATE TABLE IF NOT EXISTS investment_strategies (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,

    -- Strategy Criteria
    max_purchase_price DECIMAL(12,2),
    min_arv DECIMAL(12,2),
    max_repair_cost DECIMAL(12,2),
    min_fix_and_flip_profit DECIMAL(8,2),
    min_rental_roi DECIMAL(8,2),
    max_cash_on_cash DECIMAL(8,2),

    -- Property Preferences
    preferred_bedrooms INT,
    preferred_bathrooms INT,
    min_square_feet INT,
    max_square_feet INT,
    min_year_built INT,
    property_types TEXT[],
    counties TEXT[],
    zip_codes TEXT[],

    -- Strategy Type
    strategy_type TEXT NOT NULL,

    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_investment_strategies_user_id ON investment_strategies(user_id);
CREATE INDEX idx_investment_strategies_is_active ON investment_strategies(user_id, is_active);

CREATE TRIGGER investment_strategies_updated_at
    BEFORE UPDATE ON investment_strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 9: user_watchlist
-- Purpose: Properties users are watching
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_watchlist (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    strategy_id INT REFERENCES investment_strategies(id) ON DELETE SET NULL,

    -- Alert Preferences
    price_alert_threshold DECIMAL(8,2),
    status_change_alert BOOLEAN DEFAULT true,

    notes TEXT,

    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT user_watchlist_unique UNIQUE (user_id, property_id)
);

CREATE INDEX idx_user_watchlist_user_id ON user_watchlist(user_id);
CREATE INDEX idx_user_watchlist_property_id ON user_watchlist(property_id);
CREATE INDEX idx_user_watchlist_is_active ON user_watchlist(user_id, is_active);


-- =============================================================================
-- Table 10: user_alerts
-- Purpose: Alert queue for watchlist items
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_alerts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT REFERENCES properties(id) ON DELETE CASCADE,
    watchlist_id INT REFERENCES user_watchlist(id) ON DELETE CASCADE,

    -- Alert Details
    alert_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,

    -- Property Snapshot
    property_data JSONB,

    -- Delivery
    delivered_via_push BOOLEAN DEFAULT false,
    delivered_via_email BOOLEAN DEFAULT false,
    delivered_at TIMESTAMPTZ,

    -- User Interaction
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_alerts_user_id ON user_alerts(user_id, created_at DESC);
CREATE INDEX idx_user_alerts_is_read ON user_alerts(user_id, is_read);
CREATE INDEX idx_user_alerts_property_id ON user_alerts(property_id);


-- =============================================================================
-- Table 11: user_portfolio
-- Purpose: Acquired properties tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_portfolio (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT REFERENCES properties(id) ON DELETE SET NULL,

    -- Property Details
    property_address TEXT,
    property_city TEXT,
    property_state TEXT,
    acquisition_date DATE,
    acquisition_price DECIMAL(12,2),
    estimated_repair_cost DECIMAL(12,2),
    total_investment DECIMAL(12,2),

    -- Strategy Tracking
    strategy_id INT REFERENCES investment_strategies(id) ON DELETE SET NULL,
    strategy_type TEXT,

    -- Status Tracking
    status TEXT DEFAULT 'acquired',

    -- Financials
    arv DECIMAL(12,2),
    actual_repair_cost DECIMAL(12,2),
    sale_price DECIMAL(12,2),
    sale_date DATE,
    actual_profit DECIMAL(12,2),
    actual_roi DECIMAL(8,2),

    -- Rental Tracking
    monthly_rent DECIMAL(8,2),
    rental_roi DECIMAL(8,2),
    cash_on_cash_return DECIMAL(8,2),

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_portfolio_user_id ON user_portfolio(user_id);
CREATE INDEX idx_user_portfolio_status ON user_portfolio(user_id, status);

CREATE TRIGGER user_portfolio_updated_at
    BEFORE UPDATE ON user_portfolio
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 12: shared_properties
-- Purpose: Team collaboration - property sharing
-- =============================================================================
CREATE TABLE IF NOT EXISTS shared_properties (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    shared_by_user_id TEXT NOT NULL,
    shared_with_user_id TEXT NOT NULL,

    -- Sharing Details
    share_type TEXT DEFAULT 'view',
    message TEXT,

    is_active BOOLEAN DEFAULT true,
    viewed_at TIMESTAMPTZ,

    shared_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT shared_properties_unique UNIQUE (property_id, shared_by_user_id, shared_with_user_id)
);

CREATE INDEX idx_shared_properties_shared_by ON shared_properties(shared_by_user_id);
CREATE INDEX idx_shared_properties_shared_with ON shared_properties(shared_with_user_id);
CREATE INDEX idx_shared_properties_property_id ON shared_properties(property_id);


-- =============================================================================
-- Table 13: property_comments
-- Purpose: Comments on shared properties
-- =============================================================================
CREATE TABLE IF NOT EXISTS property_comments (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    share_id INT REFERENCES shared_properties(id) ON DELETE CASCADE,

    -- Comment Details
    comment_text TEXT NOT NULL,
    parent_comment_id INT REFERENCES property_comments(id) ON DELETE CASCADE,

    -- Comment Metadata
    is_edited BOOLEAN DEFAULT false,
    edited_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_property_comments_property_id ON property_comments(property_id, created_at DESC);
CREATE INDEX idx_property_comments_user_id ON property_comments(user_id);
CREATE INDEX idx_property_comments_parent_id ON property_comments(parent_comment_id);


-- =============================================================================
-- Table 14: property_notes
-- Purpose: User notes on properties
-- =============================================================================
CREATE TABLE IF NOT EXISTS property_notes (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,

    -- Note Details
    note_text TEXT NOT NULL,
    note_type TEXT DEFAULT 'general',
    color TEXT DEFAULT 'default',
    is_pinned BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_property_notes_property_id ON property_notes(property_id, created_at DESC);
CREATE INDEX idx_property_notes_user_id ON property_notes(user_id);

CREATE TRIGGER property_notes_updated_at
    BEFORE UPDATE ON property_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Table 15: due_diligence_checklist
-- Purpose: Task tracking per property
-- =============================================================================
CREATE TABLE IF NOT EXISTS due_diligence_checklist (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,

    -- Checklist Items (JSONB for flexibility)
    checklist_items JSONB DEFAULT '{
        "title_search": false,
        "lien_check": false,
        "property_inspection": false,
        "repair_estimate": false,
        "comparable_analysis": false,
        "arv_calculation": false,
        "profit_analysis": false,
        "financing_approved": false,
        "closing_timeline": false,
        "exit_strategy": false
    }',

    -- Custom items can be added
    custom_items JSONB DEFAULT '[]',

    -- Progress
    total_items INT DEFAULT 10,
    completed_items INT DEFAULT 0,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT due_diligence_checklist_unique UNIQUE (property_id, user_id)
);

CREATE INDEX idx_due_diligence_checklist_property_id ON due_diligence_checklist(property_id);
CREATE INDEX idx_due_diligence_checklist_user_id ON due_diligence_checklist(user_id);

CREATE TRIGGER due_diligence_checklist_updated_at
    BEFORE UPDATE ON due_diligence_checklist
    FOR EACH ROW
    EXECUTE FUNCTION update_deal_features_admin_settings_updated_at();


-- =============================================================================
-- Saved Properties with Kanban Board
-- =============================================================================
CREATE TABLE IF NOT EXISTS saved_properties (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Kanban Stage
    kanban_stage TEXT DEFAULT 'researching',
    stage_order INT DEFAULT 0,

    -- Notes
    notes TEXT,

    -- Metadata
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    stage_updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT saved_properties_unique UNIQUE (user_id, property_id)
);

CREATE INDEX idx_saved_properties_user_id ON saved_properties(user_id);
CREATE INDEX idx_saved_properties_kanban_stage ON saved_properties(user_id, kanban_stage);


-- =============================================================================
-- Comments for Tables
-- =============================================================================
COMMENT ON TABLE deal_features_admin_settings IS 'Feature toggle flags and AI quality thresholds (singleton)';
COMMENT ON TABLE deal_features_county_settings IS 'County-level feature overrides';
COMMENT ON TABLE deal_features_user_preferences IS 'User-level feature preferences';
COMMENT ON TABLE market_anomalies IS 'Detected price anomaly analysis results';
COMMENT ON TABLE comparable_sales_analysis IS 'AI-powered comparable sales analysis';
COMMENT ON TABLE comparable_properties IS 'Individual comparable property data';
COMMENT ON TABLE renovation_estimates IS 'Photo-based renovation cost estimates';
COMMENT ON TABLE investment_strategies IS 'User-defined investment strategy templates';
COMMENT ON TABLE user_watchlist IS 'Properties users are watching';
COMMENT ON TABLE user_alerts IS 'Alert queue for watchlist items';
COMMENT ON TABLE user_portfolio IS 'Acquired properties tracking';
COMMENT ON TABLE shared_properties IS 'Team collaboration - property sharing';
COMMENT ON TABLE property_comments IS 'Comments on shared properties';
COMMENT ON TABLE property_notes IS 'User notes on properties';
COMMENT ON TABLE due_diligence_checklist IS 'Task tracking per property';
COMMENT ON TABLE saved_properties IS 'Saved properties with Kanban stages';

-- =============================================================================
-- Migration Complete
-- =============================================================================
