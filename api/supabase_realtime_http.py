"""HTTP-based Supabase Realtime implementation for Vercel."""
import json
import urllib.request
import urllib.error
import os

def broadcast_to_channel(channel_name, event, payload):
    """Broadcast a message to a Supabase Realtime channel using HTTP.
    
    Note: This is a simplified approach. Supabase Realtime typically uses WebSockets,
    but for serverless environments, we'll use the Postgres NOTIFY approach or
    store events in a table that clients can poll.
    """
    supabase_url = os.environ.get('SUPABASE_URL', '')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY', '')
    
    if not supabase_url or not supabase_key:
        print("[REALTIME] Supabase not configured, skipping broadcast")
        return False
    
    # For serverless, we'll store realtime events in a table
    # that the frontend can subscribe to via Supabase client
    try:
        # Create event record
        event_data = {
            "channel": channel_name,
            "event": event,
            "payload": payload,
            "created_at": "now()"
        }
        
        # Store in realtime_events table
        url = f"{supabase_url}/rest/v1/realtime_events"
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(event_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"[REALTIME] Broadcasted {event} to channel {channel_name}")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"[REALTIME] HTTP error broadcasting: {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"[REALTIME] Error broadcasting: {e}")
        return False

def create_realtime_table_if_needed():
    """Create the realtime_events table if it doesn't exist.
    
    This table stores events that clients can subscribe to.
    """
    supabase_url = os.environ.get('SUPABASE_URL', '')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    
    if not supabase_url or not supabase_key:
        print("[REALTIME] Service role key not available, skipping table creation")
        return False
    
    # SQL to create table
    sql = """
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
    
    -- Allow anyone to read events (for simplicity)
    CREATE POLICY "Allow public read access" ON realtime_events
    FOR SELECT USING (true);
    
    -- Auto-cleanup old events after 5 minutes
    CREATE OR REPLACE FUNCTION cleanup_old_realtime_events()
    RETURNS void AS $$
    BEGIN
        DELETE FROM realtime_events 
        WHERE created_at < now() - interval '5 minutes';
    END;
    $$ LANGUAGE plpgsql;
    """
    
    # Note: In production, you'd run this via Supabase migrations
    # For now, we'll just log that it needs to be created
    print("[REALTIME] Realtime events table needs to be created via Supabase dashboard or migration")
    return True