# Database Setup for Minesweeper AI Benchmark

## Overview

The platform supports both file-based storage (default) and PostgreSQL database storage. When deployed to Render with a database, all game results, evaluations, and leaderboard data will persist across deployments.

## Setting Up PostgreSQL on Render

### 1. Create the Database

1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "PostgreSQL"
3. Configure the database:
   - **Name**: `minesweeper-db`
   - **Database**: `minesweeper_benchmark`
   - **User**: `minesweeper_user`
   - **Region**: Same as your web service
   - **PostgreSQL Version**: 15 (or latest)
   - **Plan**: Free (or upgrade for production)
4. Click "Create Database"

### 2. Connect Database to Web Service

The `render.yaml` already includes the database configuration:

```yaml
databases:
  - name: minesweeper-db
    databaseName: minesweeper_benchmark
    user: minesweeper_user
    plan: free
```

And the web service environment variables:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: minesweeper-db
      property: connectionString
```

If you've already deployed the web service:
1. Go to your web service in Render
2. Go to "Environment" tab
3. Add environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Click "Add from Database" and select your PostgreSQL database

### 3. Verify Database Connection

After deployment, check the logs to confirm database initialization:

```bash
# Using the render-api-logs.sh script
./render-api-logs.sh | grep -i "database"

# Should see:
# "Initializing database connection..."
# "Database initialized successfully"
# "Storage backend initialized: database"
```

## Database Schema

The platform automatically creates these tables on first connection:

- **games**: Stores individual game sessions
- **evaluations**: Stores evaluation metrics for games
- **tasks**: Stores benchmark tasks (game configurations)
- **prompt_templates**: Stores prompt configurations
- **leaderboard_entries**: Cached leaderboard data

## Migration from File Storage

If you have existing data in file storage, it will remain accessible. The platform checks for `DATABASE_URL` on startup:
- If set: Uses PostgreSQL
- If not set: Falls back to file storage

## Troubleshooting

### Database Connection Errors

1. Check environment variables in Render dashboard
2. Ensure database is in same region as web service
3. Check database isn't suspended (free tier suspends after 90 days of inactivity)

### Performance Issues

For production use, consider upgrading to:
- **Starter** plan: Better performance, automated backups
- **Standard** plan: High availability, point-in-time recovery

## Local Development

For local development with PostgreSQL:

```bash
# Install PostgreSQL locally
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Create local database
createdb minesweeper_benchmark

# Set environment variable
export DATABASE_URL="postgresql://localhost/minesweeper_benchmark"

# Run the application
python -m src.cli.main serve
```

## Benefits of Database Storage

1. **Persistence**: Data survives deployments and container restarts
2. **Performance**: Faster queries for leaderboard and statistics
3. **Scalability**: Can handle more concurrent users
4. **Reliability**: ACID compliance and data integrity
5. **Features**: Advanced querying, relationships, and aggregations