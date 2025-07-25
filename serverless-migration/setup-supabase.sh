#!/bin/bash

echo "Setting up Supabase for Tilts Platform..."

# Check if supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "Installing Supabase CLI..."
    brew install supabase/tap/supabase
fi

# Login to Supabase
echo "Logging in to Supabase..."
supabase login

# Create new project
echo "Creating Supabase project..."
supabase projects create tilts-platform --region us-east-1

# Initialize local project
supabase init

# Create database schema
mkdir -p supabase/migrations
cat > supabase/migrations/001_initial_schema.sql << 'EOF'
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    join_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',
    host_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Players table
CREATE TABLE session_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    player_id VARCHAR(255) NOT NULL,
    player_name VARCHAR(255),
    model_name VARCHAR(100),
    is_ready BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, player_id)
);

-- Games table
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    game_state JSONB NOT NULL,
    moves JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    winner_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'in_progress'
);

-- Evaluation results
CREATE TABLE evaluation_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    player_id VARCHAR(255) NOT NULL,
    evaluation_type VARCHAR(100),
    raw_score FLOAT,
    normalized_score FLOAT,
    breakdown JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable real-time
ALTER TABLE sessions REPLICA IDENTITY FULL;
ALTER TABLE session_players REPLICA IDENTITY FULL;
ALTER TABLE games REPLICA IDENTITY FULL;

-- Create indexes
CREATE INDEX idx_sessions_join_code ON sessions(join_code);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_games_session ON games(session_id);
CREATE INDEX idx_players_session ON session_players(session_id);

-- Row Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_scores ENABLE ROW LEVEL SECURITY;

-- Policies (allow all for now, tighten in production)
CREATE POLICY "Enable all access" ON sessions FOR ALL USING (true);
CREATE POLICY "Enable all access" ON session_players FOR ALL USING (true);
CREATE POLICY "Enable all access" ON games FOR ALL USING (true);
CREATE POLICY "Enable all access" ON evaluation_scores FOR ALL USING (true);
EOF

# Apply migrations
supabase db push

# Get project URL and keys
echo "Getting project configuration..."
supabase projects list

echo "Supabase setup complete!"
echo "Save your project URL and anon key for the API configuration"