-- Create user property overrides table
-- Stores user-specific overrides for property values with history tracking
CREATE TABLE IF NOT EXISTS user_property_overrides (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  property_id INTEGER NOT NULL REFERENCES foreclosure_listings(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL CHECK (field_name IN ('approx_upset', 'judgment_amount')),
  original_value NUMERIC,
  new_value NUMERIC NOT NULL,
  previous_spread NUMERIC, -- The spread calculation at the time of override
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_property_overrides_user_property ON user_property_overrides(user_id, property_id, field_name);
CREATE INDEX IF NOT EXISTS idx_user_property_overrides_property_id ON user_property_overrides(property_id);

-- Enable RLS
ALTER TABLE user_property_overrides ENABLE ROW LEVEL SECURITY;

-- Users can only see their own overrides
CREATE POLICY "Users can view own overrides" ON user_property_overrides
  FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own overrides
CREATE POLICY "Users can insert own overrides" ON user_property_overrides
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own overrides
CREATE POLICY "Users can update own overrides" ON user_property_overrides
  FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own overrides
CREATE POLICY "Users can delete own overrides" ON user_property_overrides
  FOR DELETE USING (auth.uid() = user_id);

-- Create function to get current active override for a user/property/field
CREATE OR REPLACE FUNCTION get_active_override(
  p_user_id UUID,
  p_property_id INTEGER,
  p_field_name TEXT
) RETURNS NUMERIC AS $$
DECLARE
  v_result NUMERIC;
BEGIN
  SELECT new_value INTO v_result
  FROM user_property_overrides
  WHERE user_id = p_user_id
    AND property_id = p_property_id
    AND field_name = p_field_name
  ORDER BY created_at DESC
  LIMIT 1;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get override history
CREATE OR REPLACE FUNCTION get_override_history(
  p_user_id UUID,
  p_property_id INTEGER,
  p_field_name TEXT
) RETURNS TABLE (
  id BIGINT,
  original_value NUMERIC,
  new_value NUMERIC,
  previous_spread NUMERIC,
  notes TEXT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    o.id,
    o.original_value,
    o.new_value,
    o.previous_spread,
    o.notes,
    o.created_at
  FROM user_property_overrides o
  WHERE o.user_id = p_user_id
    AND o.property_id = p_property_id
    AND o.field_name = p_field_name
  ORDER BY o.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
