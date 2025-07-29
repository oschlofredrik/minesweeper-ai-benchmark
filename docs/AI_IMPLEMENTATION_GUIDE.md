# AI Implementation Guide

## Overview
This guide outlines the standard approach for implementing AI features in the Tilts platform using the latest Vercel AI SDK.

## Key Principle: Use Vercel AI SDK

**IMPORTANT**: All AI integrations must use the Vercel AI SDK. Do not implement direct HTTP calls to AI provider APIs.

## Why Vercel AI SDK?

1. **Unified Interface**: Consistent API across all providers (OpenAI, Anthropic, DeepSeek, etc.)
2. **Built-in Streaming**: Real-time response streaming out of the box
3. **Error Handling**: Robust retry logic and error management
4. **Type Safety**: Full TypeScript support with proper types
5. **Edge Runtime**: Optimized for Vercel's edge functions
6. **Tool Calling**: Standardized function/tool calling across providers
7. **Reasoning Support**: Built-in support for reasoning models (o1, o3, R1)
8. **Structured Output**: Type-safe JSON generation with Zod schemas

## Installation

### TypeScript/JavaScript Projects
```bash
# Core SDK and main providers
pnpm add ai@beta @ai-sdk/openai@beta @ai-sdk/anthropic@beta @ai-sdk/react@beta zod

# Additional providers
pnpm add @ai-sdk/deepseek@beta @ai-sdk/groq@beta @ai-sdk/mistral@beta @ai-sdk/togetherai@beta

# For Replicate models
pnpm add @ai-sdk/replicate@beta

# For OpenAI-compatible endpoints
pnpm add @ai-sdk/openai-compatible@beta
```

### Python Projects (API endpoints)
```bash
# For Python-based Vercel functions
pip install openai anthropic
```

## Implementation Patterns

### 1. Basic Text Generation
```typescript
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';

// Simple generation
const { text } = await generateText({
  model: openai('gpt-4.5-preview'),
  prompt: 'Explain the rules of Minesweeper',
});

// With messages format
const { text } = await generateText({
  model: anthropic('claude-3-7-sonnet-20250219-v1:0'),
  messages: [
    { role: 'system', content: 'You are a Minesweeper expert.' },
    { role: 'user', content: 'What is the optimal opening move?' }
  ],
});
```

### 2. Streaming Responses
```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const stream = await streamText({
  model: openai('gpt-4.5-preview'),
  messages: [{ role: 'user', content: prompt }],
  temperature: 0.7,
  maxTokens: 1000,
});

// Process stream
for await (const textPart of stream.textStream) {
  console.log(textPart);
}

// Get full response
const { text, usage, finishReason } = await stream;
```

### 3. Tool Calling for Game Moves
```typescript
import { generateText, tool } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

// Define game move tool
const makeMove = tool({
  description: 'Make a move in Minesweeper',
  parameters: z.object({
    action: z.enum(['reveal', 'flag', 'unflag']),
    row: z.number().min(0).describe('Row index (0-based)'),
    col: z.number().min(0).describe('Column index (0-based)'),
    reasoning: z.string().describe('Explanation for this move'),
  }),
  execute: async ({ action, row, col, reasoning }) => {
    // Execute the move in the game
    const result = await gameEngine.makeMove(action, row, col);
    return {
      success: result.valid,
      gameState: result.newState,
      message: result.message,
    };
  },
});

// Use with multi-step for complete game
const result = await generateText({
  model: openai('gpt-4.5-preview'),
  messages: [
    { role: 'system', content: MINESWEEPER_SYSTEM_PROMPT },
    { role: 'user', content: `Game state: ${JSON.stringify(gameState)}` }
  ],
  tools: { makeMove },
  maxSteps: 50, // Allow up to 50 moves
  toolChoice: 'required', // Force tool usage
});
```

### 4. Structured Output with Zod
```typescript
import { generateObject } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

// Define structured schema
const gameAnalysisSchema = z.object({
  safeSquares: z.array(z.object({
    row: z.number(),
    col: z.number(),
    confidence: z.number().min(0).max(1),
  })),
  mineLocations: z.array(z.object({
    row: z.number(),
    col: z.number(),
    confidence: z.number().min(0).max(1),
  })),
  strategy: z.string(),
  riskAssessment: z.enum(['low', 'medium', 'high']),
});

const { object: analysis } = await generateObject({
  model: openai('gpt-4.5-preview'),
  schema: gameAnalysisSchema,
  prompt: `Analyze this Minesweeper board: ${JSON.stringify(board)}`,
});

// Use the typed result
console.log(`Found ${analysis.safeSquares.length} safe squares`);
```

### 5. Reasoning Models (o1, o3, R1)
```typescript
import { generateText, wrapLanguageModel, extractReasoningMiddleware } from 'ai';
import { openai } from '@ai-sdk/openai';
import { deepseek } from '@ai-sdk/deepseek';

// OpenAI o3-mini with reasoning effort control
const { reasoning, text } = await generateText({
  model: openai('o3-mini'),
  prompt: 'Solve this Minesweeper puzzle with perfect logic',
  providerOptions: {
    openai: { 
      reasoningEffort: 'high' // 'low', 'medium', or 'high'
    },
  },
});

console.log('Reasoning:', reasoning);
console.log('Solution:', text);

// DeepSeek R1 with reasoning extraction
const r1Model = wrapLanguageModel({
  model: deepseek('deepseek-reasoner'),
  middleware: extractReasoningMiddleware({ tagName: 'think' }),
});

const { reasoning: r1Reasoning, text: r1Text } = await generateText({
  model: r1Model,
  prompt: 'What is the optimal Minesweeper strategy?',
});
```

### 6. Extended Thinking (Claude 4)
```typescript
import { anthropic, AnthropicProviderOptions } from '@ai-sdk/anthropic';
import { generateText } from 'ai';

const { text, reasoning, reasoningDetails } = await generateText({
  model: anthropic('claude-4-sonnet-20250514'),
  prompt: 'Design a perfect Minesweeper AI algorithm',
  providerOptions: {
    anthropic: {
      thinking: { 
        type: 'enabled', 
        budgetTokens: 20000 // Allow extensive thinking
      },
    } satisfies AnthropicProviderOptions,
  },
  headers: {
    'anthropic-beta': 'interleaved-thinking-2025-05-14',
  },
});

console.log('Thought process:', reasoningDetails);
console.log('Final algorithm:', text);
```

### 7. Multi-Provider Pattern
```typescript
type AIProvider = 'openai' | 'anthropic' | 'deepseek' | 'groq';

function getModel(provider: AIProvider, modelName?: string) {
  switch (provider) {
    case 'openai':
      return openai(modelName || 'gpt-4.5-preview');
    case 'anthropic':
      return anthropic(modelName || 'claude-3-7-sonnet-20250219-v1:0');
    case 'deepseek':
      return deepseek(modelName || 'deepseek-reasoner');
    case 'groq':
      return groq(modelName || 'llama-3.1-70b-versatile');
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

// Usage
const result = await generateText({
  model: getModel(userSelectedProvider),
  messages: gameMessages,
});
```

## React Integration

### useChat Hook for Game UI
```tsx
'use client';

import { useChat } from '@ai-sdk/react';
import { useState } from 'react';

export function MinesweeperAI() {
  const [gameState, setGameState] = useState(initialGameState);
  
  const { messages, input, handleInputChange, handleSubmit, isLoading, append } = useChat({
    api: '/api/minesweeper-ai',
    body: {
      gameState,
      difficulty: 'expert',
    },
    onFinish: (message) => {
      // Update game state based on AI move
      if (message.toolInvocations) {
        const lastMove = message.toolInvocations[message.toolInvocations.length - 1];
        if (lastMove?.result?.gameState) {
          setGameState(lastMove.result.gameState);
        }
      }
    },
  });

  return (
    <div className="minesweeper-ai">
      <GameBoard state={gameState} />
      <div className="ai-controls">
        <button 
          onClick={() => append({ role: 'user', content: 'Make next move' })}
          disabled={isLoading}
        >
          {isLoading ? 'AI Thinking...' : 'AI Move'}
        </button>
      </div>
      <div className="ai-reasoning">
        {messages.map(m => (
          <div key={m.id}>
            {m.role}: {m.content}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### useObject Hook for Structured Data
```tsx
import { useObject } from '@ai-sdk/react';
import { gameAnalysisSchema } from './schemas';

export function GameAnalyzer({ board }) {
  const { object, isLoading, error, submit } = useObject({
    api: '/api/analyze-game',
    schema: gameAnalysisSchema,
  });

  return (
    <div>
      <button onClick={() => submit({ board })}>
        Analyze Board
      </button>
      {isLoading && <div>Analyzing...</div>}
      {object && (
        <div>
          <h3>Safe Moves: {object.safeSquares.length}</h3>
          <h3>Risk Level: {object.riskAssessment}</h3>
          <p>{object.strategy}</p>
        </div>
      )}
    </div>
  );
}
```

## API Route Implementation

### Next.js App Router
```typescript
// app/api/minesweeper-ai/route.ts
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(req: Request) {
  const { messages, gameState } = await req.json();

  const result = streamText({
    model: openai('gpt-4.5-preview'),
    messages: [
      {
        role: 'system',
        content: 'You are an expert Minesweeper player. Analyze the board and make optimal moves.',
      },
      ...messages,
      {
        role: 'user',
        content: `Current game state: ${JSON.stringify(gameState)}`,
      },
    ],
    tools: minesweeperTools,
    maxSteps: 10,
  });

  return result.toDataStreamResponse();
}
```

### Vercel Python Functions
```python
# api/evaluate.py
from http.server import BaseHTTPRequestHandler
import json
from ai import generateText
from ai.providers import openai

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Parse request
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Use AI SDK pattern (conceptual - adapt to Python SDK when available)
        result = generateText(
            model=openai('gpt-4'),
            messages=data['messages']
        )
        
        # Return response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'text': result.text,
            'usage': result.usage
        }).encode())
```

## Error Handling

```typescript
import { APICallError } from 'ai';

async function safeGenerateText(params: any) {
  try {
    return await generateText(params);
  } catch (error) {
    if (error instanceof APICallError) {
      console.error('API Error Details:', {
        message: error.message,
        statusCode: error.statusCode,
        responseBody: error.responseBody,
        cause: error.cause,
      });
      
      // Handle specific errors
      switch (error.statusCode) {
        case 429:
          // Rate limit - implement exponential backoff
          await delay(1000 * Math.pow(2, retryCount));
          return safeGenerateText(params);
        case 401:
          throw new Error('Invalid API key. Please check your configuration.');
        case 400:
          throw new Error('Invalid request. Check your prompt and parameters.');
        default:
          throw new Error(`AI service error: ${error.message}`);
      }
    }
    throw error;
  }
}
```

## Testing

```typescript
import { mockId, mockStreamText } from 'ai/test';

describe('Minesweeper AI', () => {
  it('should make valid moves', async () => {
    const result = await mockStreamText({
      model: openai('gpt-4'),
      messages: [{ role: 'user', content: 'Make a move' }],
      tools: minesweeperTools,
    });

    expect(result.toolCalls).toHaveLength(1);
    expect(result.toolCalls[0].toolName).toBe('makeMove');
  });
});
```

## Performance Optimization

### 1. Model Selection Strategy
```typescript
function selectOptimalModel(requirements: GameRequirements) {
  // For fast, simple moves
  if (requirements.speed === 'fast' && requirements.complexity === 'low') {
    return openai('gpt-3.5-turbo');
  }
  
  // For complex reasoning
  if (requirements.reasoning === 'deep') {
    return openai('o3-mini');
  }
  
  // For cost-effective batch processing
  if (requirements.budget === 'low' && requirements.batch) {
    return groq('llama-3.1-70b-versatile');
  }
  
  // Default high-quality model
  return openai('gpt-4.5-preview');
}
```

### 2. Caching Strategy
```typescript
import { LRUCache } from 'lru-cache';

const moveCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 60, // 1 hour
});

async function getCachedMove(gameState: GameState) {
  const cacheKey = hashGameState(gameState);
  
  if (moveCache.has(cacheKey)) {
    return moveCache.get(cacheKey);
  }
  
  const move = await generateMove(gameState);
  moveCache.set(cacheKey, move);
  return move;
}
```

### 3. Parallel Processing
```typescript
async function evaluateMultipleGames(games: Game[]) {
  // Process games in parallel with concurrency limit
  const results = await pLimit(5)(
    games.map(game => () => evaluateGame(game))
  );
  
  return results;
}
```

## Monitoring and Observability

```typescript
const result = await generateText({
  model: openai('gpt-4'),
  messages,
  experimental_telemetry: {
    isEnabled: true,
    functionId: 'minesweeper-move',
    metadata: {
      gameId: game.id,
      difficulty: game.difficulty,
      moveNumber: game.moves.length,
    },
  },
});

// Log performance metrics
console.log('AI Performance:', {
  model: result.modelId,
  latency: result.responseMs,
  tokens: result.usage,
  finishReason: result.finishReason,
});
```

## Do's and Don'ts

### Do's
- ✅ Use Vercel AI SDK for all AI integrations
- ✅ Leverage streaming for better user experience
- ✅ Use structured output with Zod schemas
- ✅ Implement proper error handling
- ✅ Choose appropriate models for each use case
- ✅ Monitor usage and costs
- ✅ Cache responses when appropriate
- ✅ Use reasoning models for complex logic

### Don'ts
- ❌ Don't make direct HTTP calls to AI APIs
- ❌ Don't parse AI responses manually
- ❌ Don't ignore rate limits
- ❌ Don't use expensive models for simple tasks
- ❌ Don't store API keys in code
- ❌ Don't skip error handling
- ❌ Don't process large batches synchronously

## Resources

- [Vercel AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Provider Reference](https://sdk.vercel.ai/providers)
- [Streaming Guide](https://sdk.vercel.ai/docs/concepts/streaming)
- [Tool Calling](https://sdk.vercel.ai/docs/concepts/tools)
- [Structured Generation](https://sdk.vercel.ai/docs/concepts/structured-generation)
- [Examples](https://github.com/vercel/ai/tree/main/examples)
- [Cookbook](https://sdk.vercel.ai/examples)