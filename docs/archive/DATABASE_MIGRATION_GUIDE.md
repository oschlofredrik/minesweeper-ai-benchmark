# Database Migration Guide - Multi-Game Support

## Overview

This guide explains the database schema updates to support multiple games in the Tilts platform.

## New Tables

### 1. **games_registry**
Central registry of all available games in the platform.
- `game_name`: Unique identifier (e.g., 'minesweeper', 'sudoku')
- `display_name`: Human-readable name
- `supported_modes`: JSON array of game modes
- `scoring_components`: JSON array of scoring metrics
- `is_active`: Whether game is currently available

### 2. **competition_sessions**
Manages competition sessions (replacing single-game focus).
- `session_id`: Unique session identifier
- `join_code`: Short code for players to join
- `format`: Competition format (single_round, tournament, etc.)
- `status`: Current status (waiting, active, completed)
- `config`: Full session configuration as JSON

### 3. **session_rounds**
Individual rounds within a competition.
- Links to `competition_sessions` and `games_registry`
- `round_number`: Sequential round number
- `game_config`: Game-specific configuration
- `scoring_profile`: Scoring weights for this round

### 4. **session_players**
Players participating in a session.
- `player_id`: Player identifier
- `ai_model`: Selected AI model
- `warmup_score`: Practice score before competition
- `final_rank`: Final position in competition

### 5. **prompt_library**
Saved prompts with version control.
- `owner_id`: Who created the prompt
- `game_name`: Which game it's for
- `visibility`: Privacy settings (private, public, etc.)
- `version`: Version number for tracking changes
- `parent_id`: Links to previous version
- Performance metrics tracked

### 6. **spectator_sessions**
Spectators watching competitions.
- `view_mode`: How they're viewing (overview, focus, etc.)
- `prediction_score`: Points from predictions
- `watch_time`: Total viewing time

### 7. **scoring_profiles**
Reusable scoring configurations.
- Pre-defined profiles (Speed Demon, Perfectionist, etc.)
- Custom profiles created by users
- `weights`: JSON object with component weights

### 8. **player_profiles**
Player accounts and statistics.
- `username`: Unique login name
- `skill_ratings`: Per-game skill ratings
- `achievements`: Unlocked achievements
- `stats`: Detailed performance statistics

### 9. **queue_items**
Evaluation queue tracking.
- `priority`: Queue priority (high, normal, low)
- `status`: Current status in queue
- Worker assignment and timing tracking

## Updated Tables

### **games** table
Added columns:
- `game_name`: Which game was played
- `session_id`: Link to competition session
- `round_number`: Which round of competition
- `ai_model`: Model used
- `score_components`: Breakdown of scoring
- `final_score`: Calculated final score

### **leaderboard_entries** table
Added columns:
- `game_name`: Separate leaderboards per game
- `scoring_profile`: Which scoring system was used
- `score_components`: Detailed score breakdown
- Updated unique constraint to include game_name

## Migration Process

### 1. Backup Database
```bash
cp minesweeper_benchmark.db minesweeper_benchmark.db.backup
```

### 2. Run Migration Script
```bash
python scripts/migrate_to_multi_game.py
```

This script will:
- Create backup automatically
- Run Alembic migration
- Populate games registry
- Update existing data (set game_name='minesweeper')
- Verify migration success

### 3. Verify Migration
The script checks that:
- All new tables exist
- Required columns are added
- Data is properly migrated

## Data Compatibility

### Existing Data
- All existing games marked as 'minesweeper'
- Existing leaderboard entries preserved
- No data loss during migration

### Default Values
- `game_name` defaults to 'minesweeper' for compatibility
- Existing sessions can continue working
- API backward compatibility maintained

## API Changes Required

After database migration, update these endpoints:

### Game-Agnostic Endpoints
- `/api/games` - List available games
- `/api/play/{game_name}` - Start specific game
- `/api/leaderboard/{game_name}` - Game-specific leaderboard
- `/api/sessions` - Competition session management

### New Endpoints
- `/api/prompt-library` - Manage saved prompts
- `/api/scoring-profiles` - Available scoring systems
- `/api/player-profiles` - Player statistics
- `/api/spectator/{session_id}` - Spectator access

## Example Usage

### Create Multi-Game Session
```python
from src.core.database_models import CompetitionSession, SessionRound

session = CompetitionSession(
    session_id='abc123',
    name='Logic Masters Tournament',
    format='multi_round',
    join_code='PLAY123'
)

# Add rounds with different games
round1 = SessionRound(
    session_id='abc123',
    round_number=1,
    game_name='minesweeper',
    game_config={'difficulty': 'medium'}
)

round2 = SessionRound(
    session_id='abc123',
    round_number=2,
    game_name='number_puzzle',
    game_config={'difficulty': 'hard'}
)
```

### Query Game-Specific Leaderboard
```python
from src.core.database_models import LeaderboardEntry

# Get Sudoku leaderboard
sudoku_leaders = session.query(LeaderboardEntry)\
    .filter_by(game_name='sudoku')\
    .order_by(LeaderboardEntry.avg_score.desc())\
    .limit(10)\
    .all()
```

## Rollback Process

If issues occur:

1. Stop the application
2. Restore backup:
   ```bash
   cp minesweeper_benchmark.db.backup minesweeper_benchmark.db
   ```
3. Or use Alembic downgrade:
   ```bash
   alembic downgrade -1
   ```

## Testing

After migration, test:
1. Existing Minesweeper games still work
2. Can create multi-game sessions
3. Leaderboards show correctly per game
4. Prompt library saves and retrieves
5. Player profiles track statistics

## Next Steps

1. Update API endpoints to use new schema
2. Modify frontend to support game selection
3. Implement remaining game plugins
4. Add more scoring profiles
5. Enable prompt sharing features