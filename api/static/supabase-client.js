// Supabase client for realtime updates
let supabaseClient = null;
let gameChannel = null;

// Initialize Supabase client
async function initSupabase() {
    try {
        // Check if Supabase SDK is loaded
        if (!window.supabase || !window.supabase.createClient) {
            console.error('Supabase SDK not loaded');
            return null;
        }
        
        // Get Supabase config from backend
        const response = await fetch('/api/config/supabase');
        if (!response.ok) {
            console.error('Failed to get Supabase config:', response.status);
            return null;
        }
        
        const config = await response.json();
        if (!config.url || !config.anonKey) {
            console.error('Invalid Supabase config:', config);
            return null;
        }
        
        // Create Supabase client
        const { createClient } = window.supabase;
        supabaseClient = createClient(config.url, config.anonKey);
        
        console.log('Supabase client initialized');
        return supabaseClient;
    } catch (error) {
        console.error('Error initializing Supabase:', error);
        return null;
    }
}

// Subscribe to game updates (polling approach for serverless)
async function subscribeToGame(jobId, onUpdate) {
    if (!supabaseClient) {
        console.error('Supabase client not initialized');
        return;
    }
    
    // Clear any existing polling
    if (gameChannel) {
        clearInterval(gameChannel);
    }
    
    let lastEventId = null;
    const channelName = `game:${jobId}`;
    
    // Poll for new events
    gameChannel = setInterval(async () => {
        try {
            // Query for new events
            let query = supabaseClient
                .from('realtime_events')
                .select('*')
                .eq('channel', channelName)
                .order('created_at', { ascending: true });
            
            // Only get events newer than last seen
            if (lastEventId) {
                const { data: lastEvent } = await supabaseClient
                    .from('realtime_events')
                    .select('created_at')
                    .eq('id', lastEventId)
                    .single();
                
                if (lastEvent) {
                    query = query.gt('created_at', lastEvent.created_at);
                }
            }
            
            const { data: events, error } = await query;
            
            if (error) {
                console.error('Error polling events:', error);
                return;
            }
            
            // Log polling status
            if (events && events.length > 0) {
                console.log(`Found ${events.length} new events`);
            }
            
            // Process new events
            for (const event of events || []) {
                console.log(`Event received: ${event.event}`, event.payload);
                onUpdate(event.event, event.payload);
                lastEventId = event.id;
            }
            
        } catch (error) {
            console.error('Error in event polling:', error);
        }
    }, 500); // Poll every 500ms for near-realtime updates
    
    console.log(`Started polling for game events: ${channelName}`);
}

// Unsubscribe from game updates
async function unsubscribeFromGame() {
    if (gameChannel) {
        clearInterval(gameChannel);
        gameChannel = null;
    }
}

// Export functions
window.initSupabase = initSupabase;
window.subscribeToGame = subscribeToGame;
window.unsubscribeFromGame = unsubscribeFromGame;