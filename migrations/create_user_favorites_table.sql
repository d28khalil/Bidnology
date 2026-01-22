-- Create user_favorites table for star/favorite functionality
-- This table stores which properties each user has favorited

CREATE TABLE IF NOT EXISTS public.user_favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    property_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure a user can only favorite a property once
    UNIQUE(user_id, property_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON public.user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_property_id ON public.user_favorites(property_id);

-- Add comments
COMMENT ON TABLE public.user_favorites IS 'User favorited properties (star functionality)';
COMMENT ON COLUMN public.user_favorites.user_id IS 'Clerk user ID';
COMMENT ON COLUMN public.user_favorites.property_id IS 'Reference to foreclosure_listings.id';

-- Enable Row Level Security
ALTER TABLE public.user_favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only see/modify their own favorites
CREATE POLICY "Users can view their own favorites"
    ON public.user_favorites FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own favorites"
    ON public.user_favorites FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own favorites"
    ON public.user_favorites FOR DELETE
    USING (auth.uid()::text = user_id);

-- Service role can bypass RLS for backend operations
-- (handled by SUPABASE_SERVICE_ROLE_KEY in the backend)
