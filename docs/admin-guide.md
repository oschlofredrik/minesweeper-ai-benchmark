# Admin Panel Guide

## Accessing the Admin Panel

The admin panel is accessible via the "Admin" link in the left sidebar of the main interface. No authentication is currently required (add authentication for production deployments).

## Admin Panel Sections

### 1. Prompts Management

Manage prompt templates used for different models.

**Features:**
- Create new prompt templates
- Edit existing templates
- Toggle active/inactive status
- Configure function calling support
- Test prompts with different models

**Best Practices:**
- Keep system prompts concise and clear
- Use `{board_state}` placeholder in user prompts
- Test prompts before marking as active
- Document changes in description field

### 2. Models Configuration

Configure AI models and their settings.

**Features:**
- Add new model configurations
- Set temperature and max tokens
- Configure API keys (optional)
- Enable/disable models
- Set provider-specific parameters

**Supported Providers:**
- OpenAI (GPT-4, GPT-3.5, o1, o3)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)

### 3. System Settings

Global configuration options for the platform.

**Available Settings:**
- `default_temperature`: Default temperature for models (0.0-2.0)
- `max_moves_per_game`: Maximum moves allowed per game
- `evaluation_timeout`: Timeout for evaluations in seconds
- `use_function_calling_default`: Enable function calling by default
- `reasoning_judge_model`: Model to use for reasoning evaluation

### 4. Feature Toggles

Enable or disable platform features.

**Available Features:**
- **Function Calling**: Use structured function calling for moves
- **Reasoning Judge**: Enable AI-based reasoning quality evaluation
- **Advanced Metrics**: Calculate MineBench composite scores
- **Episode Logging**: Save detailed game logs in JSONL format

### 5. Database Management

Complete control over games and leaderboard data.

#### Database Overview
- Total games played
- Games won/lost breakdown
- Games by model
- Leaderboard entries count

#### Games Management

**Filtering Options:**
- By model name
- By provider (OpenAI/Anthropic)
- By outcome (won/lost)

**Actions:**
- View individual game details
- Delete specific games
- Bulk delete by criteria
- See if game has full transcript

#### Leaderboard Management

**Features:**
- View all leaderboard entries
- See detailed metrics per model
- Reset model statistics (removes all games)
- Delete leaderboard entry (keeps games)

**Reset vs Delete:**
- **Reset**: Deletes ALL games for a model + removes from leaderboard
- **Delete**: Only removes leaderboard entry, keeps game history

#### Database Cleanup

**Options:**
- Delete orphaned evaluations
- Remove games without moves
- Clean up unused tasks

### 6. Export/Import

Backup and restore configuration.

**Export Includes:**
- All prompt templates
- Model configurations
- System settings
- Feature toggles

**Import Process:**
1. Select JSON configuration file
2. Preview changes
3. Import overwrites existing configuration

## Database Migration

For existing deployments, run the migration script to add new columns:

```bash
# Set your database URL
export DATABASE_URL=postgresql://user:pass@host/db

# Run migration
python scripts/migrate_db_add_columns.py
```

## Troubleshooting

### Database Not Available
If you see "Database not available" messages:
1. Check DATABASE_URL environment variable
2. Verify PostgreSQL connection
3. Run migration script if needed

### API Errors
If models fail with API errors:
1. Check API keys in environment variables
2. Verify model names are correct
3. Check rate limits with provider
4. Review error logs for details

### Missing Columns
If you see column errors in logs:
1. Run the migration script
2. Use safe endpoints temporarily
3. Check migration output for errors

## Best Practices

1. **Regular Backups**: Export configuration regularly
2. **Test Changes**: Test prompts and settings before production
3. **Monitor Logs**: Check logs for errors and warnings
4. **Clean Data**: Periodically clean up failed games
5. **Fair Evaluation**: Ensure technical failures don't affect scores

## Security Considerations

For production deployments:
1. Add authentication to admin routes
2. Use HTTPS for all connections
3. Secure database credentials
4. Limit admin access by IP if possible
5. Audit admin actions in logs