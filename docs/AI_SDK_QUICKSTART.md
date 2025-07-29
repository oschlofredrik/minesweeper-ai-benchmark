# Vercel AI SDK Quick Start Guide

Get up and running with AI-powered game evaluations in minutes using the Vercel AI SDK.

## Prerequisites

- Node.js 18+ or Python 3.9+
- Vercel account (for deployment)
- API keys for AI providers (OpenAI, Anthropic, etc.)

## 1. Installation

### For New Projects

```bash
# Create a new Next.js project with AI SDK
pnpm create next-app --example https://github.com/vercel/ai/tree/main/examples/next-openai tilts-ai-app
cd tilts-ai-app

# Install additional providers
pnpm add @ai-sdk/anthropic@beta @ai-sdk/deepseek@beta zod
```

### For Existing Tilts Project

```bash
# Navigate to your project
cd tilts

# Install AI SDK packages
pnpm add ai@beta @ai-sdk/openai@beta @ai-sdk/anthropic@beta @ai-sdk/react@beta zod

# For Python API endpoints
cd api && pip install -r requirements.txt
```

## 2. Configure Environment Variables

Create or update `.env.local`:

```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional providers
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...

# Supabase (for database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

## 3. Quick Examples

### Basic Minesweeper Move Generation

```typescript
// api/generate-move.ts
import { generateObject } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

const moveSchema = z.object({
  action: z.enum(['reveal', 'flag']),
  row: z.number(),
  col: z.number(),
  reasoning: z.string(),
});

export async function POST(req: Request) {
  const { gameState } = await req.json();
  
  const { object: move } = await generateObject({
    model: openai('gpt-4.5-preview'),
    schema: moveSchema,
    prompt: `Analyze this Minesweeper game and make the best move:
    ${JSON.stringify(gameState)}`,
  });
  
  return Response.json(move);
}
```

### Streaming Game Evaluation

```typescript
// api/evaluate-streaming.ts
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(req: Request) {
  const { gameConfig } = await req.json();
  
  const result = streamText({
    model: openai('gpt-4.5-preview'),
    messages: [
      {
        role: 'system',
        content: 'You are an expert Minesweeper player. Play the game step by step.',
      },
      {
        role: 'user',
        content: `Start a new game with config: ${JSON.stringify(gameConfig)}`,
      },
    ],
    maxSteps: 50,
  });
  
  return result.toDataStreamResponse();
}
```

### React Component with Real-time Updates

```tsx
// components/AIGamePlayer.tsx
'use client';

import { useChat } from '@ai-sdk/react';

export function AIGamePlayer() {
  const { messages, isLoading, append } = useChat({
    api: '/api/evaluate-streaming',
  });
  
  const startGame = () => {
    append({
      role: 'user',
      content: 'Start a new expert Minesweeper game',
    });
  };
  
  return (
    <div>
      <button onClick={startGame} disabled={isLoading}>
        {isLoading ? 'AI Playing...' : 'Start AI Game'}
      </button>
      
      <div className="game-log">
        {messages.map((m) => (
          <div key={m.id}>
            {m.role}: {m.content}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 4. Advanced Features

### Using Reasoning Models (o3-mini)

```typescript
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const { reasoning, text } = await generateText({
  model: openai('o3-mini'),
  prompt: 'Solve this Minesweeper puzzle optimally',
  providerOptions: {
    openai: { reasoningEffort: 'high' },
  },
});

console.log('AI reasoning:', reasoning);
console.log('Solution:', text);
```

### Extended Thinking (Claude 4)

```typescript
import { anthropic } from '@ai-sdk/anthropic';
import { generateText } from 'ai';

const { text, reasoning } = await generateText({
  model: anthropic('claude-4-sonnet-20250514'),
  prompt: 'Design the perfect Minesweeper strategy',
  providerOptions: {
    anthropic: {
      thinking: { type: 'enabled', budgetTokens: 15000 },
    },
  },
  headers: {
    'anthropic-beta': 'interleaved-thinking-2025-05-14',
  },
});
```

### Multi-Step Game Playing

```typescript
import { generateText, tool } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

const makeMove = tool({
  description: 'Make a move in the game',
  parameters: z.object({
    action: z.enum(['reveal', 'flag']),
    row: z.number(),
    col: z.number(),
  }),
  execute: async (params) => {
    // Execute move and return new game state
    return gameEngine.makeMove(params);
  },
});

const result = await generateText({
  model: openai('gpt-4.5-preview'),
  messages: [{ role: 'user', content: 'Play Minesweeper' }],
  tools: { makeMove },
  maxSteps: 100, // Play complete game
});
```

## 5. Deploy to Vercel

```bash
# Install Vercel CLI
pnpm install -g vercel

# Deploy
vercel

# Add environment variables in Vercel dashboard
# Settings → Environment Variables → Add all API keys
```

## 6. Testing Your Setup

### Test API Endpoint
```bash
curl -X POST http://localhost:3000/api/generate-move \
  -H "Content-Type: application/json" \
  -d '{
    "gameState": {
      "board": [[0,0,0],[0,1,0],[0,0,0]],
      "revealed": [[false,false,false],[false,true,false],[false,false,false]]
    }
  }'
```

### Test in Browser
1. Start dev server: `pnpm dev`
2. Open http://localhost:3000
3. Click "Start AI Game"
4. Watch the AI play in real-time

## 7. Common Patterns

### Model Selection Helper
```typescript
export function selectModel(task: 'fast' | 'reasoning' | 'complex') {
  switch (task) {
    case 'fast':
      return openai('gpt-3.5-turbo');
    case 'reasoning':
      return openai('o3-mini');
    case 'complex':
      return anthropic('claude-4-sonnet-20250514');
  }
}
```

### Error Handling
```typescript
import { APICallError } from 'ai';

try {
  const result = await generateText({...});
} catch (error) {
  if (error instanceof APICallError) {
    if (error.statusCode === 429) {
      // Handle rate limit
    } else if (error.statusCode === 401) {
      // Handle auth error
    }
  }
}
```

### Structured Game Analysis
```typescript
const analysisSchema = z.object({
  safeMoves: z.array(z.object({
    row: z.number(),
    col: z.number(),
    confidence: z.number(),
  })),
  strategy: z.string(),
  winProbability: z.number(),
});

const { object: analysis } = await generateObject({
  model: openai('gpt-4.5-preview'),
  schema: analysisSchema,
  prompt: 'Analyze the current game position',
});
```

## 8. Best Practices

1. **Start Simple**: Begin with basic text generation before adding streaming
2. **Use Structured Output**: Leverage Zod schemas for type-safe responses
3. **Handle Errors**: Always wrap AI calls in try-catch blocks
4. **Monitor Usage**: Track token usage and costs
5. **Cache When Possible**: Store results for identical game states
6. **Choose Models Wisely**: Use cheaper models for simple tasks

## 9. Troubleshooting

### "API key not found"
- Check `.env.local` file exists and contains keys
- Restart dev server after adding keys
- Verify keys are valid in provider dashboards

### "Rate limit exceeded"
- Implement exponential backoff
- Use different API keys for development
- Consider using Groq for high-volume testing

### "Function invocation failed" (Vercel)
- Check logs in Vercel dashboard
- Ensure all dependencies are in package.json
- Verify environment variables are set in Vercel

### "Streaming not working"
- Ensure using `streamText` not `generateText`
- Check client is handling streaming response
- Verify CORS headers are set correctly

## 10. Next Steps

1. **Explore Examples**: Check `/examples` directory
2. **Read Full Docs**: [AI SDK Documentation](https://sdk.vercel.ai/docs)
3. **Join Community**: [Discord](https://vercel.com/discord)
4. **Experiment**: Try different models and providers
5. **Optimize**: Implement caching and parallel processing
6. **Monitor**: Set up observability and logging

## Quick Command Reference

```bash
# Development
pnpm dev              # Start dev server
pnpm build            # Build for production
pnpm test             # Run tests

# AI SDK specific
pnpm add ai@beta      # Update to latest beta
pnpm add @ai-sdk/*    # Add new providers

# Deployment
vercel                # Deploy to Vercel
vercel env pull       # Pull env vars locally
vercel logs           # View function logs
```

## Example Projects

- [Basic Minesweeper AI](/examples/basic-minesweeper)
- [Streaming Evaluation](/examples/streaming-eval)
- [Multi-Model Comparison](/examples/model-comparison)
- [React Game UI](/examples/react-game-ui)

Happy coding! 🚀