-- Tilts Platform Database Schema

-- Sessions table
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    join_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    game_type VARCHAR(50) NOT NULL,
    format VARCHAR(50) DEFAULT 'single_round',
    max_players INTEGER DEFAULT 10,
    difficulty VARCHAR(20) DEFAULT 'medium',
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'waiting',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ
);

-- Games table
CREATE TABLE games (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(50),
    session_id VARCHAR(36) REFERENCES sessions(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20),
    model_name VARCHAR(100),
    model_provider VARCHAR(50),
    status VARCHAR(20) DEFAULT 'in_progress',
    won BOOLEAN,
    total_moves INTEGER DEFAULT 0,
    valid_moves INTEGER DEFAULT 0,
    mines_identified INTEGER DEFAULT 0,
    mines_total INTEGER DEFAULT 0,
    duration FLOAT,
    moves JSONB DEFAULT '[]',
    full_transcript JSONB,
    reasoning_scores JSONB,
    final_board_state TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leaderboard entries
CREATE TABLE leaderboard_entries (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) UNIQUE NOT NULL,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0,
    valid_move_rate FLOAT DEFAULT 0,
    mine_identification_precision FLOAT DEFAULT 0,
    mine_identification_recall FLOAT DEFAULT 0,
    coverage_ratio FLOAT DEFAULT 0,
    reasoning_score FLOAT DEFAULT 0,
    composite_score FLOAT DEFAULT 0,
    total_moves INTEGER DEFAULT 0,
    valid_moves INTEGER DEFAULT 0,
    mines_identified INTEGER DEFAULT 0,
    mines_total INTEGER DEFAULT 0,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evaluations table
CREATE TABLE evaluations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    game_type VARCHAR(50) DEFAULT 'minesweeper',
    author VARCHAR(100) DEFAULT 'anonymous',
    metrics JSONB DEFAULT '[]',
    weights JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT TRUE,
    is_imported BOOLEAN DEFAULT FALSE,
    source_id VARCHAR(36),
    usage_count INTEGER DEFAULT 0,
    rating FLOAT DEFAULT 0,
    ratings JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompts table
CREATE TABLE prompts (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    game_type VARCHAR(50) DEFAULT 'minesweeper',
    author VARCHAR(100) DEFAULT 'anonymous',
    tags JSONB DEFAULT '[]',
    variables JSONB DEFAULT '{}',
    example_output TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    forked_from VARCHAR(36),
    likes INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session players
CREATE TABLE session_players (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES sessions(id) ON DELETE CASCADE,
    player_id VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    model VARCHAR(100),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, player_id)
);

-- Settings table
CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_sessions_join_code ON sessions(join_code);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_games_session ON games(session_id);
CREATE INDEX idx_games_job ON games(job_id);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_model ON games(model_name);
CREATE INDEX idx_evaluations_game_type ON evaluations(game_type);
CREATE INDEX idx_evaluations_public ON evaluations(is_public);
CREATE INDEX idx_prompts_game_type ON prompts(game_type);
CREATE INDEX idx_prompts_public ON prompts(is_public);
CREATE INDEX idx_prompts_author ON prompts(author);

-- Enable Row Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Create policies (open access for now, can be restricted later)
CREATE POLICY "Enable read access for all" ON sessions FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all" ON sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all" ON sessions FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all" ON sessions FOR DELETE USING (true);

CREATE POLICY "Enable read access for all" ON games FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all" ON games FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all" ON games FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all" ON games FOR DELETE USING (true);

CREATE POLICY "Enable read access for all" ON leaderboard_entries FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all" ON leaderboard_entries FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all" ON leaderboard_entries FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all" ON evaluations FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all" ON evaluations FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all" ON evaluations FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all" ON evaluations FOR DELETE USING (true);

CREATE POLICY "Enable read access for all" ON prompts FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all" ON prompts FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all" ON prompts FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all" ON prompts FOR DELETE USING (true);

CREATE POLICY "Enable all access" ON session_players FOR ALL USING (true);
CREATE POLICY "Enable all access" ON settings FOR ALL USING (true);

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leaderboard_updated_at BEFORE UPDATE ON leaderboard_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluations_updated_at BEFORE UPDATE ON evaluations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompts_updated_at BEFORE UPDATE ON prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default settings
INSERT INTO settings (key, value) VALUES 
    ('features', '{"competitions": true, "evaluations": true, "marketplace": true, "admin": true}'),
    ('models', '{"openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"], "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]}'),
    ('api_keys', '{}')
ON CONFLICT (key) DO NOTHING;

-- Insert demo leaderboard data
INSERT INTO leaderboard_entries (model_name, games_played, wins, losses, win_rate, valid_move_rate, mine_identification_precision) VALUES
    ('gpt-4', 250, 213, 37, 0.85, 0.98, 0.92),
    ('claude-3-opus', 200, 164, 36, 0.82, 0.97, 0.90)
ON CONFLICT (model_name) DO NOTHING;