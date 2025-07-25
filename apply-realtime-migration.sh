#!/bin/bash

# Apply the realtime events migration to Supabase

echo "Applying realtime events migration to Supabase..."

# Check if supabase is installed
if ! command -v supabase &> /dev/null; then
    echo "Error: Supabase CLI not found. Please install it first:"
    echo "brew install supabase/tap/supabase"
    exit 1
fi

# Apply the migration
echo "Running migration 002_realtime_events.sql..."
supabase db push --password '/vETxuZ??DExSr8'

echo "Migration complete!"
echo ""
echo "The realtime_events table has been created."
echo "Frontend will poll this table for live game updates."