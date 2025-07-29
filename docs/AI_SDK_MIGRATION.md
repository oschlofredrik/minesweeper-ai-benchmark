# Vercel AI SDK Migration Guide

## Overview
This guide covers migrating to the latest Vercel AI SDK beta for improved streaming, multi-step evaluations, and advanced AI features.

**IMPORTANT**: Always use the Vercel AI SDK instead of direct HTTP API calls. The SDK provides better error handling, streaming support, and standardized interfaces across providers.

## Installation

### Latest Beta Version
```bash
# Install core SDK and providers
pnpm add ai@beta @ai-sdk/openai@beta @ai-sdk/anthropic@beta @ai-sdk/react@beta

# Additional providers
pnpm add @ai-sdk/deepseek@beta @ai-sdk/groq@beta @ai-sdk/mistral@beta

# For structured output
pnpm add zod
```

### Python Environment (for API endpoints)
```bash
cd api
pip install -r requirements.txt
```

## New Features

### 1. Advanced Models Support
- **OpenAI**: GPT-4.5, o1, o3-mini with reasoning capabilities
- **Anthropic**: Claude 4, Sonnet 3.7 with extended thinking
- **DeepSeek**: R1 reasoning model
- **Computer Use**: Claude 3.5 Sonnet with computer interaction

### 2. Streaming Evaluations
```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const stream = streamText({
  model: openai('gpt-4.5-preview'),
  messages: [{ role: 'user', content: prompt }],
  maxSteps: 10, // Enable multi-step agentic behavior
});

for await (const part of stream.textStream) {
  console.log(part);
}
```

### 3. Reasoning Models
```typescript
import { generateText, wrapLanguageModel, extractReasoningMiddleware } from 'ai';
import { openai } from '@ai-sdk/openai';

// For o1/o3 models with reasoning
const { reasoning, text } = await generateText({
  model: openai('o3-mini'),
  prompt: 'Explain quantum entanglement',
  providerOptions: {
    openai: { reasoningEffort: 'medium' }, // low, medium, high
  },
});

// For DeepSeek R1 with reasoning extraction
const enhancedModel = wrapLanguageModel({
  model: deepseek('deepseek-reasoner'),
  middleware: extractReasoningMiddleware({ tagName: 'think' }),
});

const { reasoning, text } = await generateText({
  model: enhancedModel,
  prompt: 'Solve this complex problem...',
});
```

### 4. Extended Thinking (Claude 4)
```typescript
import { anthropic, AnthropicProviderOptions } from '@ai-sdk/anthropic';
import { generateText } from 'ai';

const { text, reasoning, reasoningDetails } = await generateText({
  model: anthropic('claude-4-sonnet-20250514'),
  prompt: 'How will quantum computing impact cryptography by 2050?',
  providerOptions: {
    anthropic: {
      thinking: { type: 'enabled', budgetTokens: 15000 },
    } satisfies AnthropicProviderOptions,
  },
  headers: {
    'anthropic-beta': 'interleaved-thinking-2025-05-14',
  },
});
```

### 5. Computer Use (Anthropic)
```typescript
import { generateText, tool } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const computerTool = tool({
  description: 'Control computer actions',
  parameters: z.object({
    action: z.enum(['screenshot', 'click', 'type', 'move']),
    coordinates: z.object({ x: z.number(), y: z.number() }).optional(),
    text: z.string().optional(),
  }),
  execute: async (params) => {
    // Implementation for computer control
    return { success: true, result: 'Action completed' };
  },
});

const result = await generateText({
  model: anthropic('claude-3-5-sonnet-20241022'),
  prompt: 'Open the browser and navigate to vercel.com',
  tools: { computer: computerTool },
  maxSteps: 10,
});
```

## API Endpoints

### POST /api/evaluate-sdk
Enhanced SDK-powered evaluation with latest features.

```typescript
// Request
{
  "game": "minesweeper",
  "provider": "openai",
  "model": "gpt-4.5-preview", // or "o3-mini", "claude-4-sonnet", etc.
  "num_games": 10,
  "difficulty": "medium",
  "use_sdk": true,
  "features": {
    "streaming": true,
    "reasoning": true,
    "multiStep": true,
    "maxSteps": 50
  }
}

// Response
{
  "evaluation_id": "eval_123",
  "status": "started",
  "endpoint": "/api/evaluation/eval_123",
  "streamEndpoint": "/api/evaluation/eval_123/stream"
}
```

### GET /api/evaluation/{id}/status
Real-time evaluation progress.

```typescript
{
  "status": "running",
  "progress": 0.5,
  "games_completed": 5,
  "games_total": 10,
  "currentGame": {
    "id": "game_5",
    "moves": 23,
    "status": "in_progress",
    "reasoning": "Analyzing mine patterns..."
  }
}
```

## Frontend Integration

### React Component with Streaming
```tsx
'use client';

import { useChat } from '@ai-sdk/react';

export function GameEvaluator() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, error } = useChat({
    api: '/api/evaluate-sdk',
    streamProtocol: 'text',
  });

  return (
    <div>
      {messages.map(message => (
        <div key={message.id}>
          {message.role}: {message.content}
        </div>
      ))}
      <form onSubmit={handleSubmit}>
        <input 
          value={input} 
          onChange={handleInputChange}
          placeholder="Configure evaluation..."
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Running...' : 'Start Evaluation'}
        </button>
      </form>
      {error && <div>Error: {error.message}</div>}
    </div>
  );
}
```

### Structured Output for Game Moves
```typescript
import { generateObject } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

const moveSchema = z.object({
  action: z.enum(['reveal', 'flag']),
  row: z.number().min(0).max(15),
  col: z.number().min(0).max(29),
  reasoning: z.string(),
  confidence: z.number().min(0).max(1),
});

const { object: move } = await generateObject({
  model: openai('gpt-4.5-preview'),
  schema: moveSchema,
  prompt: `Current game state: ${JSON.stringify(gameState)}. What's your next move?`,
});

// Execute the structured move
await executeMove(move);
```

## Environment Variables

### Required
```bash
# Core AI providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Additional providers (optional)
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
MISTRAL_API_KEY=...

# Feature flags
ENABLE_REASONING=true
ENABLE_STREAMING=true
ENABLE_COMPUTER_USE=false
```

### Vercel Configuration
Add these to your Vercel project settings:
1. Go to Settings → Environment Variables
2. Add each API key
3. Select appropriate environments (Production/Preview/Development)

## Migration Checklist

### From Direct HTTP Calls
- [ ] Remove `urllib`, `requests`, or `fetch` calls to AI APIs
- [ ] Install Vercel AI SDK packages
- [ ] Replace with SDK client imports
- [ ] Update error handling to use SDK patterns
- [ ] Test streaming functionality
- [ ] Verify tool calling works correctly

### Code Updates
```typescript
// ❌ Old approach
const response = await fetch('https://api.openai.com/v1/chat/completions', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${apiKey}` },
  body: JSON.stringify({ model: 'gpt-4', messages })
});

// ✅ New approach
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const { text } = await generateText({
  model: openai('gpt-4'),
  messages,
});
```

### Feature Adoption
1. **Streaming**: Use `streamText` for real-time responses
2. **Tools**: Define tools with Zod schemas for type safety
3. **Multi-step**: Set `maxSteps` for agentic behavior
4. **Reasoning**: Enable for o1/o3/R1 models
5. **Structured Output**: Use `generateObject` for JSON responses

## Best Practices

### Model Selection
```typescript
function selectModel(requirements: ModelRequirements) {
  if (requirements.reasoning && requirements.fast) {
    return openai('o3-mini');
  }
  if (requirements.computerUse) {
    return anthropic('claude-3-5-sonnet-20241022');
  }
  if (requirements.extendedThinking) {
    return anthropic('claude-4-sonnet-20250514');
  }
  if (requirements.costEffective) {
    return groq('llama-3.1-70b-versatile');
  }
  return openai('gpt-4.5-preview'); // Default
}
```

### Error Handling
```typescript
import { APICallError } from 'ai';

try {
  const result = await generateText({
    model: openai('gpt-4'),
    prompt,
  });
} catch (error) {
  if (error instanceof APICallError) {
    console.error('API Error:', error.message);
    console.error('Status:', error.statusCode);
    console.error('Details:', error.responseBody);
    
    // Handle specific errors
    if (error.statusCode === 429) {
      // Rate limit - implement backoff
    } else if (error.statusCode === 401) {
      // Invalid API key
    }
  }
  throw error;
}
```

### Performance Optimization
1. **Batch requests** when possible
2. **Use streaming** for better perceived performance
3. **Cache responses** for repeated queries
4. **Choose appropriate models** for the task
5. **Monitor token usage** to control costs

## Monitoring and Observability

### Built-in Telemetry
```typescript
const result = await generateText({
  model: openai('gpt-4'),
  prompt,
  experimental_telemetry: { 
    isEnabled: true,
    functionId: 'evaluate-game',
    metadata: { gameId, difficulty }
  }
});
```

### Custom Logging
```typescript
import { createCallbacksTransformer } from 'ai';

const loggingTransformer = createCallbacksTransformer({
  onStart: (params) => console.log('Starting:', params),
  onCompletion: (params) => console.log('Completed:', params),
  onError: (error) => console.error('Error:', error),
});

const result = await generateText({
  model: openai('gpt-4'),
  prompt,
  experimental_transform: loggingTransformer,
});
```

## Resources
- [Vercel AI SDK Docs](https://sdk.vercel.ai/docs)
- [Provider Reference](https://sdk.vercel.ai/providers)
- [Streaming Guide](https://sdk.vercel.ai/docs/concepts/streaming)
- [Tool Calling](https://sdk.vercel.ai/docs/concepts/tools)
- [Cookbook Examples](https://sdk.vercel.ai/examples)

## Support
- [GitHub Issues](https://github.com/vercel/ai/issues)
- [Discord Community](https://vercel.com/discord)
- [API Status](https://status.openai.com/)