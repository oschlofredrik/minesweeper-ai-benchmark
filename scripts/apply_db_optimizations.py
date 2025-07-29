#!/usr/bin/env python3
"""Apply database optimizations to the Tilts platform."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api.db_migrations import migration_manager, migrate_up, migration_status
    from api.cache_service import cache
    from api.db_optimized import get_db_stats
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

def main():
    """Apply database optimizations."""
    print("=== Tilts Database Optimization Script ===\n")
    
    # Check migration status
    print("1. Checking migration status...")
    status = migration_status()
    print(f"   Total migrations: {status['total_migrations']}")
    print(f"   Applied migrations: {status['applied_migrations']}")
    print(f"   Pending migrations: {status['pending_migrations']}")
    
    if status['pending_migrations'] > 0:
        print(f"\n   Pending: {', '.join(status['pending'])}")
        
        # Generate SQL script
        print("\n2. Generating migration SQL script...")
        sql_script = migration_manager.generate_migration_script()
        
        # Save to file
        output_file = Path("apply_optimizations.sql")
        with open(output_file, 'w') as f:
            f.write(sql_script)
        
        print(f"   SQL script saved to: {output_file}")
        print("\n   To apply migrations:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Copy and paste the contents of apply_optimizations.sql")
        print("   4. Execute the script")
    else:
        print("\n   ✓ All migrations are up to date!")
    
    # Test database optimizations
    print("\n3. Testing database optimization features...")
    
    try:
        # Get database stats
        stats = get_db_stats()
        print("\n   Database Statistics:")
        print(f"   - Has Supabase: {stats['has_supabase']}")
        print(f"   - Connection pool size: {stats['connection_pool']['size']}")
        print(f"   - Available connections: {stats['connection_pool']['available']}")
        print(f"   - Cache entries: {stats['cache_info']['size']}")
        print(f"   - Cache TTL: {stats['cache_info']['ttl']}s")
        print(f"   - Leaderboard cache TTL: {stats['cache_info']['leaderboard_ttl']}s")
        
        # Show query performance if available
        if stats['query_stats']:
            print("\n   Query Performance:")
            for query_type, perf in stats['query_stats'].items():
                print(f"   - {query_type}:")
                print(f"     Count: {perf['count']}")
                print(f"     Avg: {perf['avg_duration']:.3f}s")
                print(f"     P95: {perf['p95_duration']:.3f}s")
    except Exception as e:
        print(f"\n   ⚠ Error testing optimizations: {e}")
    
    # Configuration recommendations
    print("\n4. Configuration Recommendations:")
    print("\n   Environment Variables (add to .env or Vercel):")
    print("   - DB_POOL_SIZE=5  # Connection pool size")
    print("   - DB_TIMEOUT=30  # Connection timeout in seconds")
    print("   - CACHE_TTL=300  # General cache TTL in seconds")
    print("   - LEADERBOARD_CACHE_TTL=60  # Leaderboard cache TTL")
    print("   - LEADERBOARD_BATCH_SIZE=10  # Batch update size")
    print("   - LEADERBOARD_UPDATE_INTERVAL=30  # Batch interval in seconds")
    
    # Redis setup (optional)
    print("\n   For Redis caching (optional):")
    print("   - REDIS_URL=redis://localhost:6379  # Redis connection URL")
    print("   - CACHE_PREFIX=tilts:  # Cache key prefix")
    
    # Performance tips
    print("\n5. Performance Tips:")
    print("   - Monitor slow queries in the Supabase dashboard")
    print("   - Use the /api/leaderboard?stats=true endpoint to check cache performance")
    print("   - Consider enabling Redis for production deployments")
    print("   - Review and optimize queries that appear in P95 statistics")
    
    print("\n=== Optimization setup complete! ===")

if __name__ == "__main__":
    main()