-- pg_cron Migration for Scheduled Scraping
-- Creates scheduled jobs to trigger scraping every 4 hours
--
-- Prerequisites:
-- 1. pg_cron extension must be installed: CREATE EXTENSION pg_cron;
-- 2. Server must be able to make HTTP requests to webhook endpoint
-- 3. Environment variable SCHEDULE_SECRET must be set

-- ============================================================================
-- ENABLE pg_cron EXTENSION
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- ============================================================================
-- SCHEDULED SCRAPING JOBS
-- ============================================================================

-- Schedule scraping every 4 hours (at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
-- This job triggers the /webhooks/scheduled endpoint which scrapes all 16 NJ counties

SELECT cron.schedule(
    'scrape-all-counties-every-4-hours',
    '0 */4 * * *',  -- Every 4 hours
    $$
    SELECT
        net.http_post(
            'https://your-domain.com/webhooks/scheduled'::text,
            headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
            body: '{}'::jsonb,
            timeout_milliseconds := 300000  -- 5 minute timeout
        );
    $$
);

-- ============================================================================
-- OPTIONAL: Individual County Scheduled Scraping
-- ============================================================================

-- If you want to scrape specific counties on different schedules,
-- uncomment and modify the examples below:

-- Example: Scrape high-volume counties every 2 hours
/*
SELECT cron.schedule(
    'scrape-essex-county-every-2-hours',
    '0 */2 * * *',
    $$
    SELECT net.http_post(
        'https://your-domain.com/trigger/Essex'::text,
        headers: '{"X-Webhook-Secret": "YOUR_WEBHOOK_SECRET"}'::jsonb,
        body: '{"incremental": true}'::jsonb
    );
    $$
);

SELECT cron.schedule(
    'scrape-middlesex-county-every-2-hours',
    '30 */2 * * *',
    $$
    SELECT net.http_post(
        'https://your-domain.com/trigger/Middlesex'::text,
        headers: '{"X-Webhook-Secret": "YOUR_WEBHOOK_SECRET"}'::jsonb,
        body: '{"incremental": true}'::jsonb
    );
    $$
);
*/

-- ============================================================================
-- MONITORING QUERIES
-- ============================================================================

-- View all scheduled jobs
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 100;

-- View scheduled jobs
-- SELECT * FROM cron.schedule;

-- Manually trigger a test scrape (useful for debugging)
-- SELECT net.http_post(
--     'https://your-domain.com/webhooks/scheduled',
--     headers: '{"X-Schedule-Secret": "YOUR_SCHEDULE_SECRET"}'::jsonb,
--     body: '{}'::jsonb
-- );

-- ============================================================================
-- CLEANUP (if needed)
-- ============================================================================

-- To remove a scheduled job:
-- SELECT cron.unschedule('scrape-all-counties-every-4-hours');

-- To remove all pg_cron jobs (use with caution):
-- TRUNCATE cron.schedule;
