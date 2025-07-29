"""Database migration system for Tilts platform."""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

if HAS_SUPABASE:
    try:
        from supabase import create_client, Client
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except ImportError:
        HAS_SUPABASE = False
        supabase = None
else:
    supabase = None

class Migration:
    """Represents a database migration."""
    
    def __init__(self, version: str, name: str, sql: str):
        self.version = version
        self.name = name
        self.sql = sql
        self.applied_at = None
    
    def __repr__(self):
        return f"<Migration {self.version}: {self.name}>"

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, migrations_dir: str = "supabase/migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations = []
        self._load_migrations()
    
    def _load_migrations(self):
        """Load all migration files."""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return
        
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        for file_path in migration_files:
            # Parse version and name from filename (e.g., "001_initial_schema.sql")
            filename = file_path.stem
            parts = filename.split("_", 1)
            
            if len(parts) >= 2:
                version = parts[0]
                name = parts[1]
            else:
                version = filename
                name = filename
            
            # Read SQL content
            with open(file_path, 'r') as f:
                sql = f.read()
            
            migration = Migration(version, name, sql)
            self.migrations.append(migration)
        
        logger.info(f"Loaded {len(self.migrations)} migrations")
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        if not HAS_SUPABASE:
            # For JSON fallback, track in a file
            migrations_file = Path("/tmp/tilts_db/applied_migrations.txt")
            if migrations_file.exists():
                with open(migrations_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
            return []
        
        try:
            # Check if migrations table exists
            result = supabase.table('migrations').select('version').execute()
            return [m['version'] for m in (result.data or [])]
        except:
            # Table doesn't exist, create it
            self._create_migrations_table()
            return []
    
    def _create_migrations_table(self):
        """Create migrations tracking table."""
        if not HAS_SUPABASE:
            return
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            version VARCHAR(20) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        try:
            # Execute raw SQL (note: this requires admin access)
            # For production, this should be done via Supabase dashboard
            logger.info("Migrations table should be created via Supabase dashboard")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
    
    def _record_migration(self, migration: Migration):
        """Record that a migration has been applied."""
        if not HAS_SUPABASE:
            # For JSON fallback, append to file
            migrations_file = Path("/tmp/tilts_db/applied_migrations.txt")
            migrations_file.parent.mkdir(exist_ok=True)
            with open(migrations_file, 'a') as f:
                f.write(f"{migration.version}\n")
            return
        
        try:
            supabase.table('migrations').insert({
                'version': migration.version,
                'name': migration.name
            }).execute()
        except Exception as e:
            logger.error(f"Failed to record migration {migration.version}: {e}")
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of migrations that haven't been applied yet."""
        applied = set(self._get_applied_migrations())
        pending = []
        
        for migration in self.migrations:
            if migration.version not in applied:
                pending.append(migration)
        
        return pending
    
    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration."""
        if not HAS_SUPABASE:
            logger.info(f"Would apply migration {migration.version}: {migration.name}")
            self._record_migration(migration)
            return True
        
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        try:
            # Note: For production, migrations should be applied via Supabase CLI
            # or dashboard, not through the application
            logger.warning("Migration SQL should be applied via Supabase dashboard or CLI")
            print(f"\n--- Migration {migration.version} ---")
            print(migration.sql)
            print("--- End Migration ---\n")
            
            # Record as applied (for tracking purposes)
            self._record_migration(migration)
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            return False
    
    def migrate(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Apply all pending migrations up to target version."""
        pending = self.get_pending_migrations()
        
        if target_version:
            # Filter to only migrations up to target version
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations")
            return {
                'success': True,
                'applied': [],
                'message': 'No pending migrations'
            }
        
        applied = []
        failed = None
        
        for migration in pending:
            if self.apply_migration(migration):
                applied.append(migration.version)
            else:
                failed = migration.version
                break
        
        result = {
            'success': failed is None,
            'applied': applied,
            'pending': [m.version for m in self.get_pending_migrations()],
            'message': f"Applied {len(applied)} migrations"
        }
        
        if failed:
            result['failed'] = failed
            result['message'] = f"Migration {failed} failed"
        
        return result
    
    def status(self) -> Dict[str, Any]:
        """Get migration status."""
        applied = self._get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'total_migrations': len(self.migrations),
            'applied_migrations': len(applied),
            'pending_migrations': len(pending),
            'applied': applied,
            'pending': [m.version for m in pending],
            'latest_applied': applied[-1] if applied else None,
            'next_to_apply': pending[0].version if pending else None
        }
    
    def generate_migration_script(self) -> str:
        """Generate a SQL script with all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            return "-- No pending migrations"
        
        script_parts = [
            "-- Tilts Platform Database Migrations",
            f"-- Generated at: {datetime.utcnow().isoformat()}",
            f"-- Pending migrations: {len(pending)}",
            ""
        ]
        
        for migration in pending:
            script_parts.extend([
                f"-- Migration {migration.version}: {migration.name}",
                migration.sql,
                "",
                f"-- Record migration",
                f"INSERT INTO migrations (version, name) VALUES ('{migration.version}', '{migration.name}');",
                ""
            ])
        
        return "\n".join(script_parts)

# Global migration manager instance
migration_manager = MigrationManager()

# CLI-style functions
def migrate_up(target_version: Optional[str] = None) -> Dict[str, Any]:
    """Apply pending migrations."""
    return migration_manager.migrate(target_version)

def migration_status() -> Dict[str, Any]:
    """Get migration status."""
    return migration_manager.status()

def generate_migration_sql() -> str:
    """Generate SQL script for pending migrations."""
    return migration_manager.generate_migration_script()

# Export everything
__all__ = [
    'Migration',
    'MigrationManager',
    'migration_manager',
    'migrate_up',
    'migration_status',
    'generate_migration_sql'
]