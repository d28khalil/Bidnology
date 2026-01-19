-- =============================================================================
-- Mobile Push Notifications System
-- Version: 1.0
-- Date: December 28, 2025
--
-- This migration creates tables for mobile push notifications:
-- - Device token registry for iOS/Android/Web
-- - Push notification queue with delivery tracking
-- - Integration with watchlist/alerts system
-- - Quiet hours and notification preferences
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: mobile_push_tokens
-- Description: Device tokens for push notifications (iOS, Android, Web)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mobile_push_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,

    -- Device Token
    device_token VARCHAR(500) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    CONSTRAINT platform_check
        CHECK (platform IN ('ios', 'android', 'web')),

    -- Device Information (optional, for debugging/targeting)
    device_info JSONB DEFAULT '{}',

    -- Notification Preferences
    enable_hot_deals BOOLEAN DEFAULT true,
    enable_auction_updates BOOLEAN DEFAULT true,
    enable_price_drops BOOLEAN DEFAULT true,
    enable_status_changes BOOLEAN DEFAULT true,
    enable_watchlist_alerts BOOLEAN DEFAULT true,
    enable_comps_available BOOLEAN DEFAULT false,
    enable_marketing_updates BOOLEAN DEFAULT false,

    -- Quiet Hours (users can disable notifications during certain hours)
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_timezone VARCHAR(50) DEFAULT 'America/New_York',

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, device_token)
);

CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON mobile_push_tokens(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_push_tokens_platform ON mobile_push_tokens(platform, is_active);
CREATE INDEX IF NOT EXISTS idx_push_tokens_token ON mobile_push_tokens(device_token);


-- -----------------------------------------------------------------------------
-- Table: push_notification_queue
-- Description: Queue for push notifications with delivery tracking
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS push_notification_queue (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    property_id INT,

    -- Notification Content
    notification_type VARCHAR(30) NOT NULL,
    CONSTRAINT notification_type_check
        CHECK (notification_type IN (
            'hot_deal',
            'price_drop',
            'auction_reminder',
            'status_change',
            'comps_available',
            'watchlist_alert',
            'portfolio_update',
            'marketing'
        )),

    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,

    -- Deep Link (where to navigate when tapped)
    deep_link VARCHAR(500),
    -- e.g., "bidnology://property/12345" or "https://app.bidnology.com/property/12345"

    -- Custom Data (additional payload)
    custom_data JSONB DEFAULT '{}',

    -- Priority
    priority VARCHAR(20) DEFAULT 'normal',
    CONSTRAINT priority_check
        CHECK (priority IN ('low', 'normal', 'high', 'urgent')),

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending',
    CONSTRAINT status_check
        CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'cancelled')),

    -- Delivery Tracking
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    -- When user actually tapped/opened the notification

    -- Error Handling
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,

    -- Scheduling
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    -- Can schedule for future delivery

    -- Batch ID (for grouping related notifications)
    batch_id UUID,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_push_property
        FOREIGN KEY (property_id)
        REFERENCES foreclosure_listings(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_push_queue_status ON push_notification_queue(status, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_push_queue_user ON push_notification_queue(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_queue_type ON push_notification_queue(notification_type);
CREATE INDEX IF NOT EXISTS idx_push_queue_priority ON push_notification_queue(priority, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_push_queue_batch ON push_notification_queue(batch_id);


-- -----------------------------------------------------------------------------
-- Table: push_notification_history
-- Description: Historical log of all sent notifications (analytics)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS push_notification_history (
    id SERIAL PRIMARY KEY,
    queue_id INT,

    -- Copy of notification data (for historical analysis)
    user_id UUID NOT NULL,
    property_id INT,
    notification_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,

    -- Delivery Results
    status VARCHAR(20) NOT NULL,
    platform VARCHAR(20),
    device_count INT,  -- How many devices this was sent to

    -- Engagement Metrics
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    time_to_open_seconds INT,

    -- Error Details (if failed)
    error_summary TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_push_history_queue
        FOREIGN KEY (queue_id)
        REFERENCES push_notification_queue(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_push_history_user ON push_notification_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_history_type ON push_notification_history(notification_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_history_status ON push_notification_history(status, created_at DESC);


-- -----------------------------------------------------------------------------
-- Table: push_notification_templates
-- Description: Reusable notification templates for consistency
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS push_notification_templates (
    id SERIAL PRIMARY KEY,

    -- Template Identification
    template_key VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,

    -- Notification Type
    notification_type VARCHAR(30) NOT NULL,

    -- Content Templates (Jinja2-style variables)
    title_template VARCHAR(200) NOT NULL,
    body_template TEXT NOT NULL,

    -- Template Variables (documentation)
    variables JSONB DEFAULT '{}',

    -- Default Priority
    default_priority VARCHAR(20) DEFAULT 'normal',

    -- Active Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_push_templates_type ON push_notification_templates(notification_type);
CREATE INDEX IF NOT EXISTS idx_push_templates_active ON push_notification_templates(template_key, is_active);


-- =============================================================================
-- Insert Default Notification Templates
-- =============================================================================

INSERT INTO push_notification_templates (template_key, name, notification_type, title_template, body_template, variables, default_priority) VALUES
-- Hot Deal Alert
(
    'hot_deal_alert',
    'Hot Deal Alert',
    'hot_deal',
    '🔥 Hot Deal: {property_address}',
    '{discount_percent}% below market value! Upset price: ${upset_price}. Auction: {auction_date}',
    '{"property_address": "Full property address", "discount_percent": "Discount percentage", "upset_price": "Minimum bid", "auction_date": "Sale date"}'::jsonb,
    'high'
),

-- Price Drop Alert
(
    'price_drop_alert',
    'Price Drop Alert',
    'price_drop',
    '💰 Price Drop: {property_address}',
    'Upset price reduced from ${old_price} to ${new_price}. Save ${savings}!',
    '{"property_address": "Full property address", "old_price": "Original price", "new_price": "New price", "savings": "Amount saved"}'::jsonb,
    'high'
),

-- Auction Reminder
(
    'auction_reminder',
    'Auction Reminder',
    'auction_reminder',
    '⏰ Auction in {days} days: {property_address}',
    'Don''t forget! Auction for {property_address} is on {auction_date} at {auction_time}. Upset price: ${upset_price}',
    '{"property_address": "Full property address", "days": "Days until auction", "auction_date": "Sale date", "auction_time": "Sale time", "upset_price": "Minimum bid"}'::jsonb,
    'normal'
),

-- Status Change
(
    'status_change',
    'Property Status Change',
    'status_change',
    '📋 Status Update: {property_address}',
    'Property status changed from "{old_status}" to "{new_status}"',
    '{"property_address": "Full property address", "old_status": "Previous status", "new_status": "New status"}'::jsonb,
    'normal'
),

-- Comps Available
(
    'comps_available',
    'New Comps Available',
    'comps_available',
    '📊 New Comps: {property_address}',
    '{comp_count} new comparable properties found near {property_address}. Tap to view analysis.',
    '{"property_address": "Full property address", "comp_count": "Number of new comps"}'::jsonb,
    'low'
),

-- Watchlist Alert
(
    'watchlist_alert',
    'Watchlist Alert',
    'watchlist_alert',
    '👀 Watchlist Alert: {property_address}',
    '{alert_message}: {property_address}',
    '{"property_address": "Full property address", "alert_message": "Alert details"}'::jsonb,
    'normal'
)
ON CONFLICT (template_key) DO NOTHING;


-- =============================================================================
-- Create Trigger for Updated At
-- =============================================================================

CREATE TRIGGER update_push_tokens_updated_at
    BEFORE UPDATE ON mobile_push_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_templates_updated_at
    BEFORE UPDATE ON push_notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Helper Function: Check if current time is within quiet hours
-- =============================================================================

CREATE OR REPLACE FUNCTION is_in_quiet_hours(
    p_user_id UUID,
    p_current_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS BOOLEAN AS $$
DECLARE
    v_quiet_enabled BOOLEAN;
    v_quiet_start TIME;
    v_quiet_end TIME;
    v_current_time TIME;
    v_current_timezone VARCHAR(50);
BEGIN
    -- Get user's quiet hours settings
    SELECT
        quiet_hours_enabled,
        quiet_hours_start,
        quiet_hours_end,
        quiet_timezone
    INTO
        v_quiet_enabled,
        v_quiet_start,
        v_quiet_end,
        v_current_timezone
    FROM mobile_push_tokens
    WHERE user_id = p_user_id
      AND is_active = true
    LIMIT 1;

    -- If quiet hours not enabled, return false (not in quiet hours)
    IF v_quiet_enabled IS NULL OR NOT v_quiet_enabled THEN
        RETURN false;
    END IF;

    -- Convert current time to user's timezone and extract time
    v_current_time := (p_current_time AT TIME ZONE v_current_timezone)::TIME;

    -- Check if current time is within quiet hours range
    IF v_quiet_start <= v_quiet_end THEN
        -- Normal range (e.g., 10 PM to 7 AM doesn't cross midnight)
        RETURN v_current_time >= v_quiet_start AND v_current_time <= v_quiet_end;
    ELSE
        -- Range crosses midnight (e.g., 10 PM to 7 AM)
        RETURN v_current_time >= v_quiet_start OR v_current_time <= v_quiet_end;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- Helper Function: Create notification from template
-- =============================================================================

CREATE OR REPLACE FUNCTION create_notification_from_template(
    p_user_id UUID,
    p_template_key VARCHAR(50),
    p_property_id INT DEFAULT NULL,
    p_variables JSONB DEFAULT '{}',
    p_priority VARCHAR(20) DEFAULT 'normal',
    p_scheduled_for TIMESTAMPTZ DEFAULT NOW()
)
RETURNS INT AS $$
DECLARE
    v_template RECORD;
    v_title TEXT;
    v_body TEXT;
    v_queue_id INT;
    v_variable_key TEXT;
    v_variable_value TEXT;
BEGIN
    -- Get template
    SELECT * INTO v_template
    FROM push_notification_templates
    WHERE template_key = p_template_key
      AND is_active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Template not found or inactive: %', p_template_key;
    END IF;

    -- Simple variable substitution (in production, use proper template engine)
    v_title := v_template.title_template;
    v_body := v_template.body_template;

    -- Replace variables in title
    FOR v_variable_key IN SELECT jsonb_object_keys(p_variables)
    LOOP
        v_variable_value := p_variables->>v_variable_key;
        v_title := replace(v_title, '{' || v_variable_key || '}', v_variable_value);
        v_body := replace(v_body, '{' || v_variable_key || '}', v_variable_value);
    END LOOP;

    -- Insert into queue
    INSERT INTO push_notification_queue (
        user_id,
        property_id,
        notification_type,
        title,
        body,
        priority,
        scheduled_for,
        custom_data
    ) VALUES (
        p_user_id,
        p_property_id,
        v_template.notification_type,
        v_title,
        v_body,
        COALESCE(p_priority, v_template.default_priority),
        p_scheduled_for,
        p_variables
    ) RETURNING id INTO v_queue_id;

    RETURN v_queue_id;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
