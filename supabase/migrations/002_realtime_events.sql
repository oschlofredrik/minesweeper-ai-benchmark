-- Create realtime events table for serverless broadcasting
CREATE TABLE IF NOT EXISTS realtime_events (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    channel text NOT NULL,
    event text NOT NULL,
    payload jsonb,
    created_at timestamptz DEFAULT now()
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_realtime_events_channel_created 
ON realtime_events(channel, created_at DESC);

-- Enable Row Level Security
ALTER TABLE realtime_events ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read events (for development)
CREATE POLICY "Allow public read access" ON realtime_events
FOR SELECT USING (true);

-- Allow authenticated users to insert events
CREATE POLICY "Allow authenticated insert" ON realtime_events
FOR INSERT WITH CHECK (true);

-- Create function to cleanup old events
CREATE OR REPLACE FUNCTION cleanup_old_realtime_events()
RETURNS void AS $$
BEGIN
    DELETE FROM realtime_events 
    WHERE created_at < now() - interval '5 minutes';
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to cleanup old events
-- This would need to be set up via Supabase dashboard or pg_cron extension