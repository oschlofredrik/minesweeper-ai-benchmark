-- Performance optimization indexes for Tilts Platform

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_games_session_created ON games(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_games_job_created ON games(job_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_games_model_status ON games(model_name, status);
CREATE INDEX IF NOT EXISTS idx_games_created_desc ON games(created_at DESC);

-- Leaderboard performance
CREATE INDEX IF NOT EXISTS idx_leaderboard_win_rate ON leaderboard_entries(win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_composite ON leaderboard_entries(win_rate DESC, games_played DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_model_unique ON leaderboard_entries(model_name) WHERE model_name IS NOT NULL;

-- Session queries
CREATE INDEX IF NOT EXISTS idx_sessions_created_desc ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status_created ON sessions(status, created_at DESC);

-- Prompt search optimization
CREATE INDEX IF NOT EXISTS idx_prompts_likes_desc ON prompts(likes DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_game_public ON prompts(game_type, is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_prompts_author_created ON prompts(author, created_at DESC);

-- Full-text search indexes (if using PostgreSQL full-text search)
CREATE INDEX IF NOT EXISTS idx_prompts_name_gin ON prompts USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_prompts_description_gin ON prompts USING gin(to_tsvector('english', description));

-- Evaluation queries
CREATE INDEX IF NOT EXISTS idx_evaluations_usage ON evaluations(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_evaluations_game_public ON evaluations(game_type, is_public) WHERE is_public = true;

-- JSONB indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_games_moves_gin ON games USING gin(moves);
CREATE INDEX IF NOT EXISTS idx_sessions_config_gin ON sessions USING gin(config);
CREATE INDEX IF NOT EXISTS idx_prompts_tags_gin ON prompts USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_evaluations_tags_gin ON evaluations USING gin(tags);

-- Partial indexes for common filters
CREATE INDEX IF NOT EXISTS idx_games_in_progress ON games(created_at DESC) WHERE status = 'in_progress';
CREATE INDEX IF NOT EXISTS idx_games_completed ON games(created_at DESC) WHERE status IN ('won', 'lost');
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(created_at DESC) WHERE status IN ('waiting', 'active');

-- Update statistics for query planner
ANALYZE sessions;
ANALYZE games;
ANALYZE leaderboard_entries;
ANALYZE evaluations;
ANALYZE prompts;
ANALYZE session_players;
ANALYZE settings;