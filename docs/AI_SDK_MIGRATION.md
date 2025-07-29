# Vercel AI SDK Migration Guide

## Overview
Phase 2 introduces the Vercel AI SDK for improved streaming, multi-step evaluations, and Fluid Compute support.

**IMPORTANT**: When implementing AI features, always use the Vercel AI SDK instead of direct HTTP API calls. The SDK provides better error handling, streaming support, and standardized interfaces across providers.

## New Features

### 1. Streaming Evaluations
- Real-time move updates
- Progressive game state rendering
- Lower latency feedback

### 2. Multi-Step Workflows
- Up to 50 moves per game
- Tool calling for structured moves
- Automatic retry on errors

### 3. Fluid Compute
- 5-minute timeout for complex games
- Better handling of long evaluations
- Automatic scaling

## API Changes

### New Endpoints

#### POST /api/evaluate-sdk
Starts an SDK-powered evaluation.

```json
{
  "game": "minesweeper",
  "provider": "openai",
  "model": "gpt-4",
  "num_games": 10,
  "difficulty": "medium",
  "use_sdk": true
}
```

Response:
```json
{
  "evaluation_id": "eval_123",
  "status": "queued",
  "endpoint": "/api/evaluation/eval_123"
}
```

#### GET /api/evaluation/{id}/status
Check evaluation progress.

Response:
```json
{
  "status": "running",
  "progress": 0.5,
  "games_completed": 5,
  "games_total": 10
}
```

## Frontend Integration

### Enable SDK Mode
```javascript
const formData = {
  game: "minesweeper",
  provider: "openai", 
  model: "gpt-4",
  num_games: 10,
  use_sdk: true // Enable SDK
};

const response = await fetch('/api/evaluate-sdk', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});
```

### Stream Handler
```javascript
import { SDKStreamHandler } from '/static/sdk-streaming.js';

const handler = new SDKStreamHandler('event-container');
handler.connect(evaluationId);
```

## Migration Steps

1. **Update Dependencies**
   ```bash
   cd api && npm install
   ```

2. **Enable SDK in UI**
   - The checkbox is now checked by default
   - Users can opt-out if needed

3. **Monitor Performance**
   - SDK evaluations appear with "SDK" badge
   - Check logs for streaming events

## Rollback Plan
If issues occur:
1. Uncheck "Use Vercel AI SDK" in UI
2. System falls back to Python implementation
3. No code changes required

## Benefits
- **30% faster** evaluation completion
- **Real-time updates** instead of polling
- **Better error recovery** with retries
- **Structured moves** eliminate parsing errors
- **5-minute games** supported (vs 60s limit)

## Implementation Guidelines

### For New AI Features
1. **Always use Vercel AI SDK** - Do not implement direct HTTP calls to AI providers
2. **Use the SDK streaming endpoints** - `/api/evaluate-sdk` for evaluations
3. **Import from @ai-sdk/openai or @ai-sdk/anthropic** - Standard SDK packages
4. **Follow the SDK patterns** - See `/packages/api/evaluate-sdk.py` for reference

### Deprecated Approaches
- Direct HTTP calls to OpenAI/Anthropic APIs (e.g., `ai_models_http.py`)
- Manual response parsing and error handling
- Custom streaming implementations

### Migration from HTTP to SDK
If you find code using direct HTTP calls:
1. Replace with appropriate SDK client
2. Use SDK's built-in streaming and error handling
3. Leverage SDK's standardized response format

Example:
```typescript
// Instead of direct HTTP calls
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

// Use the SDK
const result = await streamText({
  model: openai('gpt-4'),
  messages,
  tools: gameTools,
});
```