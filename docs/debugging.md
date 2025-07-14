# Debugging Guide

This guide helps you debug common issues with the Minesweeper AI Benchmark platform.

## Logging System

### Structured Logging Fields

All log entries include structured fields for easy filtering:

- `timestamp`: UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `logger`: Logger name (e.g., "evaluation.runner")
- `message`: Log message
- `model_name`: The AI model being used (e.g., "gpt-4", "claude-3")
- `model_provider`: The provider (e.g., "openai", "anthropic")
- `game_num`: Which game number in the evaluation session
- `move_num`: Which move number in the current game
- `game_id`: Unique game identifier
- `job_id`: Job/session identifier
- `error_type`: Type of error when applicable

### Viewing Logs in Render

1. **Via Render Dashboard**:
   ```bash
   ./view-logs-browser.sh
   ```

2. **Via API Streaming**:
   ```bash
   export RENDER_API_KEY='your-api-key'
   ./render-api-logs.sh
   ```

3. **Filter by Model**:
   - In Render logs, search for `"model_name":"gpt-4"` to see only GPT-4 logs
   - Search for `"model_provider":"anthropic"` for all Anthropic models

## Common Issues and Solutions

### 1. AI Makes Repeated Invalid Moves

**Symptoms**:
- AI keeps trying to reveal already-revealed cells
- Same move attempted multiple times
- Game gets stuck in a loop

**Solution**: The platform now automatically handles this:
- Tracks consecutive invalid moves
- Stops after 3 invalid moves
- Marks game as ERROR (not a loss)

**Debug Info**:
```json
{
  "level": "WARNING",
  "message": "Game 1 - Invalid move attempted",
  "model_name": "gpt-3.5-turbo",
  "move_num": 5,
  "action": "reveal (0, 0)",
  "consecutive_errors": 2
}
```

### 2. Model Timeout Errors

**Symptoms**:
- Games fail with timeout errors
- Especially common with o1/o3/o4 models

**Check**:
- Model timeout configuration in admin panel
- Default timeouts: 30s (most models), 120s (o1), 300s (o3/o4)

### 3. API Authentication Errors

**Symptoms**:
- 401 Unauthorized errors
- "Invalid API key" messages

**Check**:
1. Environment variables are set correctly
2. API keys are valid and have credits
3. Keys match the provider (OpenAI key for OpenAI models)

### 4. Games Not Progressing

**Debug Steps**:
1. Check logs for the specific game:
   ```
   "game_num":1 "model_name":"gpt-4"
   ```

2. Look for move progression:
   ```
   "move_num":1 -> "move_num":2 -> etc.
   ```

3. Check for errors between moves:
   ```
   "level":"ERROR"
   ```

### 5. Leaderboard Not Updating

**Check**:
- Games must complete successfully (not ERROR status)
- Only games with status WON or LOST count
- Technical failures are excluded from stats

## Debugging Commands

### Local Testing

```bash
# Test with debug output
python debug_game.py

# Test specific model
python test_evaluation.py

# Check logs locally
tail -f logs/minesweeper.log | jq '.'
```

### Production Debugging

```bash
# Stream logs with model filter
./render-api-logs.sh | grep '"model_name":"claude-3"'

# Check recent errors
./render-api-logs.sh | grep '"level":"ERROR"' | tail -20

# Monitor specific game
./render-api-logs.sh | grep '"game_num":5'
```

## Log Analysis Tips

1. **Follow a Game Session**:
   - Filter by `job_id` to see all games in a session
   - Filter by `game_id` to see all moves in one game

2. **Identify Patterns**:
   - Look for `consecutive_errors` increasing
   - Check `move_num` to see where games get stuck
   - Compare `board_coverage` between models

3. **Performance Analysis**:
   - Filter by `model_name` and check `duration`
   - Look at `tokens_used` for cost analysis
   - Check `reasoning_length` for response quality

## Database Debugging

Access the admin panel database tab to:
- View individual game records
- Check move-by-move transcripts
- Analyze error patterns
- Clean up failed games

## Contact Support

If you encounter persistent issues:
1. Collect relevant log entries
2. Note the job_id and game_id
3. Include model name and error messages
4. Create an issue on GitHub with details