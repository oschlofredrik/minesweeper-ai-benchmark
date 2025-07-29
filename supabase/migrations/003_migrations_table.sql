-- Create migrations tracking table

CREATE TABLE IF NOT EXISTS migrations (
    version VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE migrations ENABLE ROW LEVEL SECURITY;

-- Create read-only policy for migrations (admin only should write)
CREATE POLICY "Enable read access for all" ON migrations FOR SELECT USING (true);

-- Insert existing migrations as already applied
INSERT INTO migrations (version, name) VALUES 
    ('001', 'initial_schema'),
    ('002', 'performance_indexes')
ON CONFLICT (version) DO NOTHING;

-- Add index on applied_at for ordering
CREATE INDEX idx_migrations_applied ON migrations(applied_at DESC);