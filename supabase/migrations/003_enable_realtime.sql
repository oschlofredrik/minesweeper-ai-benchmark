-- Enable Realtime for key tables
ALTER PUBLICATION supabase_realtime ADD TABLE games;
ALTER PUBLICATION supabase_realtime ADD TABLE sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE session_players;
ALTER PUBLICATION supabase_realtime ADD TABLE leaderboard_entries;
ALTER PUBLICATION supabase_realtime ADD TABLE realtime_events;

-- Create presence table for online users
CREATE TABLE IF NOT EXISTS presence (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id text NOT NULL,
    session_id text,
    status text DEFAULT 'online',
    last_seen timestamptz DEFAULT now(),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now(),
    UNIQUE(user_id, session_id)
);

-- Enable RLS
ALTER TABLE presence ENABLE ROW LEVEL SECURITY;

-- Allow public access for development
CREATE POLICY "Allow public presence access" ON presence
FOR ALL USING (true);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_presence_session_status 
ON presence(session_id, status);

-- Function to update last_seen
CREATE OR REPLACE FUNCTION update_presence_last_seen()
RETURNS trigger AS $$
BEGIN
    NEW.last_seen = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update last_seen
CREATE TRIGGER presence_last_seen_trigger
BEFORE UPDATE ON presence
FOR EACH ROW
EXECUTE FUNCTION update_presence_last_seen();

-- Function to cleanup stale presence
CREATE OR REPLACE FUNCTION cleanup_stale_presence()
RETURNS void AS $$
BEGIN
    UPDATE presence 
    SET status = 'offline'
    WHERE last_seen < now() - interval '30 seconds'
    AND status = 'online';
    
    DELETE FROM presence
    WHERE last_seen < now() - interval '5 minutes';
END;
$$ LANGUAGE plpgsql;