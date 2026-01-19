-- ============================================================================
-- V1 CONSOLIDATION MIGRATION
-- Reduces tables from 38 to 9 V1 tables
-- Moves ML/Anomaly features to V2
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE NEW user_data TABLE (combines 4 tables)
-- ============================================================================

CREATE TABLE user_data (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  property_id INTEGER NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,

  -- Saved Properties (from saved_properties)
  is_saved BOOLEAN DEFAULT FALSE,
  kanban_stage TEXT DEFAULT 'researching',
  saved_notes TEXT,

  -- Watchlist (from user_watchlist)
  is_watched BOOLEAN DEFAULT FALSE,
  watch_priority TEXT DEFAULT 'normal',
  alert_on_price_change BOOLEAN DEFAULT TRUE,
  alert_on_status_change BOOLEAN DEFAULT TRUE,
  alert_on_new_comps BOOLEAN DEFAULT FALSE,
  alert_on_auction_near BOOLEAN DEFAULT FALSE,
  auction_alert_days INTEGER DEFAULT 7,
  watch_notes TEXT,

  -- Notes (from property_notes - JSONB array)
  notes JSONB DEFAULT '[]'::jsonb,

  -- Checklist (from due_diligence_checklist - JSONB)
  checklist JSONB DEFAULT '{}'::jsonb,
  checklist_total INTEGER DEFAULT 10,
  checklist_completed INTEGER DEFAULT 0,
  checklist_completed_at TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, property_id)
);

-- Create indexes for performance
CREATE INDEX idx_user_data_user_id ON user_data(user_id);
CREATE INDEX idx_user_data_property_id ON user_data(property_id);
CREATE INDEX idx_user_data_saved ON user_data(user_id) WHERE is_saved = TRUE;
CREATE INDEX idx_user_data_watched ON user_data(user_id) WHERE is_watched = TRUE;
CREATE INDEX idx_user_data_kanban ON user_data(user_id, kanban_stage) WHERE is_saved = TRUE;

-- ============================================================================
-- PART 2: MIGRATE DATA FROM OLD TABLES TO user_data
-- ============================================================================

-- Migrate saved_properties
INSERT INTO user_data (
  user_id,
  property_id,
  is_saved,
  kanban_stage,
  saved_notes,
  created_at,
  updated_at
)
SELECT
  user_id,
  property_id,
  TRUE as is_saved,
  COALESCE(kanban_stage, 'researching') as kanban_stage,
  notes as saved_notes,
  saved_at as created_at,
  COALESCE(stage_updated_at, saved_at) as updated_at
FROM saved_properties
ON CONFLICT (user_id, property_id) DO NOTHING;

-- Migrate user_watchlist (update existing rows or insert new)
INSERT INTO user_data (
  user_id,
  property_id,
  is_watched,
  watch_priority,
  alert_on_price_change,
  alert_on_status_change,
  alert_on_new_comps,
  alert_on_auction_near,
  auction_alert_days,
  watch_notes,
  created_at,
  updated_at
)
SELECT
  user_id,
  property_id,
  TRUE as is_watched,
  priority as watch_priority,
  alert_on_price_change,
  alert_on_status_change,
  alert_on_new_comps,
  alert_on_auction_near,
  auction_alert_days,
  watch_notes,
  added_at as created_at,
  added_at as updated_at
FROM user_watchlist
ON CONFLICT (user_id, property_id) DO UPDATE SET
  is_watched = TRUE,
  watch_priority = EXCLUDED.watch_priority,
  alert_on_price_change = EXCLUDED.alert_on_price_change,
  alert_on_status_change = EXCLUDED.alert_on_status_change,
  alert_on_new_comps = EXCLUDED.alert_on_new_comps,
  alert_on_auction_near = EXCLUDED.alert_on_auction_near,
  auction_alert_days = EXCLUDED.auction_alert_days,
  watch_notes = EXCLUDED.watch_notes;

-- Migrate property_notes (merge into existing user_data records)
INSERT INTO user_data (user_id, property_id, notes, created_at, updated_at)
SELECT
  user_id,
  property_id,
  jsonb_build_array(
    jsonb_build_object(
      'id', id,
      'text', note_text,
      'type', COALESCE(note_type, 'general'),
      'color', COALESCE(color, 'default'),
      'is_pinned', COALESCE(is_pinned, FALSE),
      'created_at', created_at,
      'updated_at', updated_at
    )
  ) as notes,
  created_at,
  updated_at
FROM property_notes
ON CONFLICT (user_id, property_id) DO UPDATE SET
  notes = user_data.notes || EXCLUDED.notes;

-- Migrate due_diligence_checklist (merge into existing user_data records)
INSERT INTO user_data (user_id, property_id, checklist, checklist_total, checklist_completed, checklist_completed_at, created_at, updated_at)
SELECT
  user_id,
  property_id,
  checklist_items,
  total_items,
  completed_items,
  completed_at,
  created_at,
  updated_at
FROM due_diligence_checklist
ON CONFLICT (user_id, property_id) DO UPDATE SET
  checklist = EXCLUDED.checklist,
  checklist_total = EXCLUDED.checklist_total,
  checklist_completed = EXCLUDED.checklist_completed,
  checklist_completed_at = EXCLUDED.checklist_completed_at;

-- ============================================================================
-- PART 3: RENAME ML/ANOMALY TABLES TO v2_ PREFIX
-- ============================================================================

ALTER TABLE market_anomalies RENAME TO v2_market_anomalies;
ALTER TABLE deal_intelligence_model_weights RENAME TO v2_deal_intelligence_model_weights;
ALTER TABLE deal_intelligence_feature_importance RENAME TO v2_deal_intelligence_feature_importance;
ALTER TABLE deal_intelligence_feedback RENAME TO v2_deal_intelligence_feedback;
ALTER TABLE deal_intelligence_ranking_history RENAME TO v2_deal_intelligence_ranking_history;
ALTER TABLE deal_intelligence_exploration RENAME TO v2_deal_intelligence_exploration;
ALTER TABLE deal_intelligence_attention_scores RENAME TO v2_deal_intelligence_attention_scores;

-- ============================================================================
-- PART 4: UPDATE FOREIGN KEY CONSTRAINTS IN RENAMED TABLES
-- ============================================================================

-- v2_market_anomalies already has fk_anomaly_property pointing to foreclosure_listings - no change needed
-- v2_deal_intelligence_feedback already has fk_feedback_property - no change needed
-- v2_deal_intelligence_ranking_history already has fk_ranking_property - no change needed
-- v2_deal_intelligence_attention_scores already has fk_attention_property - no change needed

-- ============================================================================
-- PART 5: UPDATE deal_features_admin_settings (DISABLE V2 FEATURES)
-- ============================================================================

UPDATE deal_features_admin_settings SET
  feature_market_anomaly_detection = FALSE,
  feature_lock_market_anomaly_detection = TRUE,
  feature_comparable_sales_analysis = TRUE,  -- Keep V1
  feature_lock_comparable_sales_analysis = FALSE,
  updated_at = NOW()
WHERE id = 1;

-- ============================================================================
-- PART 6: CLEANUP OLD TABLES (OPTIONAL - UNCOMMENT AFTER VERIFICATION)
-- ============================================================================

-- Drop old tables after verifying data migrated successfully
-- COMMENT OUT FOR NOW - VERIFY FIRST, THEN UNCOMMENT TO DROP

-- DROP TABLE IF EXISTS saved_properties CASCADE;
-- DROP TABLE IF EXISTS user_watchlist CASCADE;
-- DROP TABLE IF EXISTS property_notes CASCADE;
-- DROP TABLE IF EXISTS due_diligence_checklist CASCADE;

-- ============================================================================
-- PART 7: CREATE HELPER FUNCTIONS FOR user_data
-- ============================================================================

-- Function to get user's kanban board
CREATE OR REPLACE FUNCTION get_user_kanban_board(p_user_id TEXT)
RETURNS JSONB AS $$
DECLARE
  result JSONB;
BEGIN
  SELECT jsonb_object_agg(
    kanban_stage,
    jsonb_agg(
      jsonb_build_object(
        'id', ud.id,
        'property_id', ud.property_id,
        'property_address', fl.property_address,
        'city', fl.city,
        'state', fl.state,
        'zip_code', fl.zip_code,
        'county_name', fl.county_name,
        'opening_bid', fl.opening_bid,
        'approx_upset', fl.approx_upset,
        'sale_date', fl.sale_date,
        'saved_notes', ud.saved_notes,
        'checklist_progress', CASE
          WHEN ud.checklist_total > 0 THEN
            round((ud.checklist_completed::NUMERIC / ud.checklist_total::NUMERIC) * 100)
          ELSE 0
        END,
        'updated_at', ud.updated_at
      )
    )
  )
  INTO result
  FROM user_data ud
  JOIN foreclosure_listings fl ON fl.id = ud.property_id
  WHERE ud.user_id = p_user_id AND ud.is_saved = TRUE
  GROUP BY kanban_stage;

  RETURN coalesce(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to update checklist progress
CREATE OR REPLACE FUNCTION update_checklist_progress(
  p_user_id TEXT,
  p_property_id INTEGER
)
RETURNS VOID AS $$
BEGIN
  UPDATE user_data
  SET
    checklist_completed = (
      SELECT count(*) FILTER (WHERE value = 'true')
      FROM jsonb_each_text(checklist)
    ),
    checklist_completed_at = CASE
      WHEN checklist_total > 0 AND (
        SELECT count(*) FILTER (WHERE value = 'true')
        FROM jsonb_each_text(checklist)
      ) >= checklist_total
      THEN NOW()
      ELSE NULL
    END,
    updated_at = NOW()
  WHERE user_id = p_user_id AND property_id = p_property_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICATION QUERIES (RUN TO VERIFY MIGRATION)
-- ============================================================================

-- Check user_data counts
-- SELECT 'user_data total' as label, COUNT(*) FROM user_data
-- UNION ALL
-- SELECT 'user_data saved', COUNT(*) FROM user_data WHERE is_saved = TRUE
-- UNION ALL
-- SELECT 'user_data watched', COUNT(*) FROM user_data WHERE is_watched = TRUE
-- UNION ALL
-- SELECT 'user_data with notes', COUNT(*) FROM user_data WHERE jsonb_array_length(notes) > 0
-- UNION ALL
-- SELECT 'user_data with checklist', COUNT(*) FROM user_data WHERE checklist != '{}'::jsonb;

-- Compare old vs new counts (before dropping old tables)
-- SELECT 'saved_properties (old)' as label, COUNT(*) FROM saved_properties
-- UNION ALL
-- SELECT 'user_watchlist (old)', COUNT(*) FROM user_watchlist
-- UNION ALL
-- SELECT 'property_notes (old)', COUNT(*) FROM property_notes
-- UNION ALL
-- SELECT 'due_diligence_checklist (old)', COUNT(*) FROM due_diligence_checklist;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
