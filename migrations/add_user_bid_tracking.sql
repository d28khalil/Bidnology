-- Add user bid tracking fields (starting_bid, bid_cap, property_sold)
-- These allow users to track their personal bidding strategy and sale outcomes

-- Drop the old CHECK constraint and add new one with additional fields
ALTER TABLE user_property_overrides DROP CONSTRAINT IF EXISTS user_property_overrides_field_name_check;

ALTER TABLE user_property_overrides
  ADD CONSTRAINT user_property_overrides_field_name_check
  CHECK (field_name IN ('approx_upset', 'judgment_amount', 'starting_bid', 'bid_cap', 'property_sold'));

-- Add comment for documentation
COMMENT ON COLUMN user_property_overrides.field_name IS 'Field being overridden: approx_upset, judgment_amount, starting_bid, bid_cap, or property_sold';
COMMENT ON COLUMN user_property_overrides.new_value IS 'New value set by user. For property_sold, this is a timestamp string or boolean true';

-- Update the get_active_override function comment
COMMENT ON FUNCTION get_active_override IS 'Get the most recent override value for a user/property/field. Supports: approx_upset, judgment_amount, starting_bid, bid_cap, property_sold';

-- Update the get_override_history function comment
COMMENT ON FUNCTION get_override_history IS 'Get complete history of overrides for a user/property/field. Supports: approx_upset, judgment_amount, starting_bid, bid_cap, property_sold';
