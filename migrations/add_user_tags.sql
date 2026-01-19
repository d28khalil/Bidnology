-- Migration: Add User Tags Feature
-- This allows users to create custom tags and apply them to properties
-- Tags are user-specific - each user has their own set of tags

-- Table: user_tags
-- Stores custom tags created by users
CREATE TABLE IF NOT EXISTS user_tags (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#3B82F6', -- Default blue color
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique tag names per user
    CONSTRAINT user_tags_user_name_unique UNIQUE (user_id, name)
);

-- Create indexes for user_tags
CREATE INDEX IF NOT EXISTS idx_user_tags_user_id ON user_tags (user_id);
CREATE INDEX IF NOT EXISTS idx_user_tags_name ON user_tags (name);

-- Table: property_tags
-- Junction table linking properties to user tags
CREATE TABLE IF NOT EXISTS property_tags (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT property_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES user_tags(id) ON DELETE CASCADE,
    CONSTRAINT property_tags_property_id_fkey FOREIGN KEY (property_id) REFERENCES foreclosure_listings(id) ON DELETE CASCADE,

    -- Ensure a user can only apply a specific tag once per property
    CONSTRAINT property_tags_user_property_tag_unique UNIQUE (user_id, property_id, tag_id)
);

-- Create indexes for property_tags
CREATE INDEX IF NOT EXISTS idx_property_tags_user_id ON property_tags (user_id);
CREATE INDEX IF NOT EXISTS idx_property_tags_property_id ON property_tags (property_id);
CREATE INDEX IF NOT EXISTS idx_property_tags_tag_id ON property_tags (tag_id);

-- Enable Row Level Security
ALTER TABLE user_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_tags ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only manage their own tags
CREATE POLICY "Users can view their own tags"
    ON user_tags FOR SELECT
    USING (user_id = current_setting('request.user.id') TEXT);

CREATE POLICY "Users can insert their own tags"
    ON user_tags FOR INSERT
    WITH CHECK (user_id = current_setting('request.user.id') TEXT);

CREATE POLICY "Users can update their own tags"
    ON user_tags FOR UPDATE
    USING (user_id = current_setting('request.user.id') TEXT);

CREATE POLICY "Users can delete their own tags"
    ON user_tags FOR DELETE
    USING (user_id = current_setting('request.user.id') TEXT);

-- RLS Policies: Users can only view/manage their own property tags
CREATE POLICY "Users can view their own property tags"
    ON property_tags FOR SELECT
    USING (user_id = current_setting('request.user.id') TEXT);

CREATE POLICY "Users can insert their own property tags"
    ON property_tags FOR INSERT
    WITH CHECK (user_id = current_setting('request.user.id') TEXT);

CREATE POLICY "Users can delete their own property tags"
    ON property_tags FOR DELETE
    USING (user_id = current_setting('request.user.id') TEXT);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_tags_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER user_tags_updated_at
    BEFORE UPDATE ON user_tags
    FOR EACH ROW
    EXECUTE FUNCTION update_user_tags_updated_at();

-- Grant permissions (if using Supabase with service role)
-- These grants are handled by Supabase automatically for authenticated users

-- Comments for documentation
COMMENT ON TABLE user_tags IS 'User-defined tags for organizing properties';
COMMENT ON TABLE property_tags IS 'Junction table linking properties to user tags';
COMMENT ON COLUMN user_tags.color IS 'Hex color code for tag display (e.g., #3B82F6)';
