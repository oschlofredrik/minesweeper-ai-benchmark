#!/bin/bash
# Apply Supabase migrations

echo "Applying database migrations to Supabase..."

# Use the password directly with supabase db push
export PGPASSWORD='/vETxuZ??DExSr8'

# Apply migrations
supabase db push --password '/vETxuZ??DExSr8'

echo "Migrations complete!"