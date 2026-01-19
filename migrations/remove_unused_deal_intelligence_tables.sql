-- =============================================================================
-- Remove Unused Deal Intelligence Tables
-- Version: 1.0
-- Date: December 28, 2025
--
-- This migration drops tables that were created but are not currently used
-- by the 4 core Deal Intelligence features:
-- 1. Market Anomaly Detection
-- 2. Comparable Sales Analysis
-- 3. Saved Properties + Kanban
-- 4. Watchlist + Alerts
-- =============================================================================

-- Drop tables in order of dependencies (child tables first)

-- Mobile Push Notifications (not implemented)
DROP TABLE IF EXISTS push_notification_queue CASCADE;
DROP TABLE IF EXISTS mobile_push_tokens CASCADE;

-- Team Collaboration (not implemented)
DROP TABLE IF EXISTS property_comments CASCADE;
DROP TABLE IF EXISTS shared_properties CASCADE;

-- Portfolio Tracking (not implemented)
DROP TABLE IF EXISTS user_portfolio CASCADE;

-- Investment Strategies (not implemented)
DROP TABLE IF EXISTS investment_strategies CASCADE;

-- Renovation Estimator (not implemented)
DROP TABLE IF EXISTS renovation_estimates CASCADE;

-- Notes & Checklist (service exists but no API routes)
DROP TABLE IF EXISTS due_diligence_checklist CASCADE;
DROP TABLE IF EXISTS property_notes CASCADE;

-- ML/Intelligence Tables (not implemented - separate feature)
DROP TABLE IF EXISTS deal_intelligence_ranking_history CASCADE;
DROP TABLE IF EXISTS deal_intelligence_exploration CASCADE;
DROP TABLE IF EXISTS deal_intelligence_feature_importance CASCADE;
DROP TABLE IF EXISTS deal_intelligence_model_weights CASCADE;
DROP TABLE IF EXISTS deal_intelligence_feedback CASCADE;
DROP TABLE IF EXISTS deal_intelligence_attention_scores CASCADE;
DROP TABLE IF EXISTS deal_intelligence_investor_criteria CASCADE;
