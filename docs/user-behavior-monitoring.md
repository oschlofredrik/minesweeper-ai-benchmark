# User Behavior Monitoring Implementation

This document describes the lightweight user behavior monitoring added to key API endpoints.

## Overview

User behavior monitoring has been added to track feature usage across the platform without adding new infrastructure. The monitoring uses the existing logging system with structured logging that includes:

- **event_type**: Categorizes the event (e.g., "user_activity", "admin_activity", "system_activity")
- **activity**: Specific action being performed
- **endpoint**: The API endpoint being accessed
- Additional contextual data specific to each endpoint

## Monitored Endpoints

### Play Sessions (`/api/play`)
- **Activities tracked**:
  - `play_session_start`: When a user starts playing games
  - `play_session_complete`: When games finish successfully
  - `play_session_failed`: When games fail with errors
- **Context logged**: model_name, provider, num_games, game_type, difficulty, user

### Competition Sessions (`/api/sessions/*`)
- **Activities tracked**:
  - `competition_created`: New competition session created
  - `competition_joined`: Player joins a session
  - `competition_started`: Competition begins
  - `session_deleted_empty`: Empty session cleanup
  - `quick_match_templates_view`: Quick match templates viewed
- **Context logged**: session details, player info, format, rounds

### Leaderboard (`/api/leaderboard`)
- **Activities tracked**:
  - `leaderboard_view`: Main leaderboard accessed
  - `game_leaderboard_view`: Game-specific leaderboard viewed
- **Context logged**: filters applied (task_type, metric, limit)

### Prompts (`/api/prompts/*`)
- **Activities tracked**:
  - `prompt_saved`: New prompt saved
  - `prompt_search`: Prompt search performed
  - `prompt_view`: Prompt details viewed
  - `prompt_fork`: Prompt forked by user
  - `prompt_like`: Prompt liked
  - `prompt_usage`: Prompt used in game
  - `prompt_recommendations`: Recommendations requested
  - `prompt_analysis`: Quality analysis requested
  - `prompt_suggestions`: Auto-complete suggestions
- **Context logged**: game_name, visibility, tags, search criteria

### Games (`/api/games/*`)
- **Activities tracked**:
  - `games_list_view`: Games catalog viewed
  - `game_play_start`: Individual game started
  - `game_templates_view`: Game templates accessed
- **Context logged**: game_name, player_id, ai_model, difficulty

### Admin (`/api/admin/*`)
- **Activities tracked**:
  - `admin_prompts_list`: Admin views prompts
  - `admin_prompt_update`: Admin updates prompt
  - `admin_feature_toggle`: Feature flag changed
  - `admin_database_stats`: Database stats viewed
- **Context logged**: specific admin actions and changes

### Other Activities
- **Task Generation**: `task_generation` when benchmark tasks are generated
- **System Activities**: `session_cleanup` for automatic cleanup

## Usage Analysis

To analyze usage patterns, filter logs by:

1. **event_type**: "user_activity" for user actions
2. **activity**: Specific activities like "play_session_start"
3. **endpoint**: API endpoints being used
4. **Time ranges**: To see usage over time

Example log query:
```bash
grep '"event_type": "user_activity"' logs/tilts_api.log | \
  jq -r '[.timestamp, .activity, .model_name // .game_name // "N/A"] | @csv'
```

## Key Metrics to Track

1. **Most Used Models**: Count play_session_start by model_name
2. **Popular Games**: Count game_play_start by game_name
3. **Feature Adoption**: Count prompt_* activities
4. **Competition Engagement**: Count competition_* activities
5. **User Flow**: Sequence of activities by user/session

## Implementation Details

- No new dependencies or infrastructure required
- Uses existing structured JSON logging
- Logs include timestamp for time-based analysis
- Extra context helps understand usage patterns
- Lightweight - just logging statements added

## Future Enhancements

1. Add user session tracking for better flow analysis
2. Create analytics dashboard from log data
3. Add more granular event tracking as needed
4. Export metrics to monitoring service