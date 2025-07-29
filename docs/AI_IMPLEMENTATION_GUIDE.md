# AI Implementation Guide

## Overview
This guide outlines the standard approach for implementing AI features in the Tilts platform.

## Key Principle: Use Vercel AI SDK

**IMPORTANT**: All AI integrations must use the Vercel AI SDK. Do not implement direct HTTP calls to AI provider APIs.

## Why Vercel AI SDK?

1. **Unified Interface**: Consistent API across all providers (OpenAI, Anthropic, etc.)
2. **Built-in Streaming**: Real-time response streaming out of the box
3. **Error Handling**: Robust retry logic and error management
4. **Type Safety**: Full TypeScript support with proper types
5. **Edge Runtime**: Optimized for Vercel's edge functions
6. **Tool Calling**: Standardized function/tool calling across providers

## Implementation Approach

### 1. Install Required Packages
```bash
npm install ai @ai-sdk/openai @ai-sdk/anthropic
```

### 2. Import SDK Clients
```typescript
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { streamText, generateText } from 'ai';
```

### 3. Use SDK Patterns
```typescript
// For streaming responses
const result = await streamText({
  model: openai('gpt-4'),
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt }
  ],
  tools: {
    makeMove: {
      description: 'Make a move in the game',
      parameters: z.object({
        action: z.enum(['reveal', 'flag']),
        row: z.number(),
        col: z.number()
      })
    }
  }
});

// For non-streaming responses
const result = await generateText({
  model: anthropic('claude-3-opus-20240229'),
  messages,
  temperature: 0.7
});
```

### 4. Handle Responses
```typescript
// Streaming
for await (const part of result.textStream) {
  console.log(part);
}

// Tool calls
for (const toolCall of result.toolCalls) {
  if (toolCall.toolName === 'makeMove') {
    await executeMove(toolCall.args);
  }
}
```

## Reference Implementation

See `/packages/api/evaluate-sdk.py` for a complete example of Vercel AI SDK usage in the evaluation system.

## Migration Checklist

If you're updating existing code:

- [ ] Remove direct HTTP calls (urllib, requests, fetch to AI APIs)
- [ ] Replace with Vercel AI SDK imports
- [ ] Update error handling to use SDK patterns
- [ ] Test streaming functionality
- [ ] Verify tool calling works correctly
- [ ] Update any documentation

## Common Patterns

### Provider Selection
```typescript
function getModel(provider: string, modelName: string) {
  switch (provider) {
    case 'openai':
      return openai(modelName);
    case 'anthropic':
      return anthropic(modelName);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}
```

### Error Handling
```typescript
try {
  const result = await streamText({
    model: getModel(provider, modelName),
    messages,
  });
} catch (error) {
  if (error.name === 'AI_APICallError') {
    // Handle API errors
  } else if (error.name === 'AI_InvalidPromptError') {
    // Handle prompt errors
  }
  throw error;
}
```

### Structured Output
```typescript
const result = await generateObject({
  model: openai('gpt-4'),
  schema: z.object({
    move: z.object({
      action: z.enum(['reveal', 'flag']),
      row: z.number(),
      col: z.number(),
      reasoning: z.string()
    })
  }),
  prompt: gameStatePrompt
});
```

## Do's and Don'ts

### Do's
- ✅ Use Vercel AI SDK for all AI integrations
- ✅ Leverage built-in streaming capabilities
- ✅ Use SDK's error handling and retry logic
- ✅ Take advantage of tool calling features
- ✅ Follow TypeScript types provided by the SDK

### Don'ts
- ❌ Don't make direct HTTP calls to OpenAI/Anthropic APIs
- ❌ Don't implement custom streaming logic
- ❌ Don't parse responses manually
- ❌ Don't handle rate limiting yourself (SDK does this)
- ❌ Don't create custom retry mechanisms

## Resources

- [Vercel AI SDK Documentation](https://sdk.vercel.ai/docs)
- [SDK Provider Reference](https://sdk.vercel.ai/providers)
- [Streaming Guide](https://sdk.vercel.ai/docs/concepts/streaming)
- [Tool Calling](https://sdk.vercel.ai/docs/concepts/tools)