-- ==============================================================================
-- NutriLens Production Database Schema & RPC Functions
-- ==============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. logged_meals Table
CREATE TABLE IF NOT EXISTS logged_meals (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    food_name TEXT NOT NULL,
    calories DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    protein_g DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    fat_g DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    carb_g DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    likes_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_logged_meals_user_created ON logged_meals (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logged_meals_public_created ON logged_meals (is_public, created_at DESC) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_logged_meals_created_at ON logged_meals (created_at DESC);

-- 2. meal_likes Table (Enforces single like per user per meal)
CREATE TABLE IF NOT EXISTS meal_likes (
    id BIGSERIAL PRIMARY KEY,
    meal_id BIGINT NOT NULL REFERENCES logged_meals(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_meal_user_like UNIQUE (meal_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_meal_likes_meal_id ON meal_likes(meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_likes_user_id ON meal_likes(user_id);

-- 3. shopping_list Table
CREATE TABLE IF NOT EXISTS shopping_list (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    item TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shopping_list_user ON shopping_list(user_id);

-- 4. chat_history Table
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id, created_at);

-- ==============================================================================
-- HARDENED ATOMIC RPC FUNCTIONS
-- ==============================================================================

-- Atomic Increment of Likes Count
-- Enforces:
-- 1. Caller authentication (auth.uid() must be non-null)
-- 2. Insertion into meal_likes occurs atomically inside same transaction
-- 3. Fixed search_path to prevent search_path injection attacks
-- 4. Restricted EXECUTE privileges
CREATE OR REPLACE FUNCTION increment_meal_likes(m_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    calling_user_id TEXT;
    new_count INTEGER;
BEGIN
    calling_user_id := auth.uid()::text;
    IF calling_user_id IS NULL OR calling_user_id = '' THEN
        RAISE EXCEPTION 'Unauthorized: Caller must be authenticated to like a meal'
            USING ERRCODE = '42501';
    END IF;

    -- Verify meal exists
    IF NOT EXISTS (SELECT 1 FROM public.logged_meals WHERE id = m_id) THEN
        RAISE EXCEPTION 'Meal with ID % does not exist', m_id
            USING ERRCODE = 'P0002';
    END IF;

    -- Insert like record first; unique constraint enforces single like per user
    INSERT INTO public.meal_likes (meal_id, user_id)
    VALUES (m_id, calling_user_id);

    -- Atomically update like counter only after successful like insertion
    UPDATE public.logged_meals
    SET likes_count = likes_count + 1
    WHERE id = m_id
    RETURNING likes_count INTO new_count;

    RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- Revoke default public execution & grant strictly to authenticated role
REVOKE EXECUTE ON FUNCTION increment_meal_likes(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION increment_meal_likes(BIGINT) TO authenticated;

-- Database-Side Leaderboard Aggregation for the Last 7 Days
CREATE OR REPLACE FUNCTION get_top_loggers_last_7_days(limit_count INTEGER DEFAULT 3)
RETURNS TABLE (
    rank BIGINT,
    user_id TEXT,
    score BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_users AS (
        SELECT
            m.user_id,
            COUNT(m.id) AS total_meals
        FROM public.logged_meals m
        WHERE m.created_at >= NOW() - INTERVAL '7 days'
        GROUP BY m.user_id
        ORDER BY total_meals DESC
        LIMIT limit_count
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY ru.total_meals DESC)::BIGINT AS rank,
        ru.user_id,
        ru.total_meals::BIGINT AS score
    FROM ranked_users ru;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

ALTER TABLE logged_meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- logged_meals policies
CREATE POLICY "Users can select own meals or public meals"
    ON logged_meals FOR SELECT
    USING (auth.uid()::text = user_id OR is_public = TRUE);

CREATE POLICY "Users can insert own meals"
    ON logged_meals FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own meals"
    ON logged_meals FOR UPDATE
    USING (auth.uid()::text = user_id);

-- meal_likes policies
CREATE POLICY "Authenticated users can view likes"
    ON meal_likes FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can like meals as themselves"
    ON meal_likes FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid()::text = user_id);

-- shopping_list policies
CREATE POLICY "Users can manage own shopping list"
    ON shopping_list FOR ALL
    USING (auth.uid()::text = user_id);

-- chat_history policies
CREATE POLICY "Users can manage own chat history"
    ON chat_history FOR ALL
    USING (auth.uid()::text = user_id);
