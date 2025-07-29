# Tilts Platform Documentation

## Overview
Tilts is a comprehensive AI evaluation platform for logic-based games, powered by Vercel AI SDK and deployed on Vercel with Supabase backend.

## Quick Links
- 🚀 [AI SDK Quick Start](AI_SDK_QUICKSTART.md) - Get started in minutes
- 📚 [AI Implementation Guide](AI_IMPLEMENTATION_GUIDE.md) - Detailed patterns and best practices
- 🔄 [AI SDK Migration Guide](AI_SDK_MIGRATION.md) - Upgrade to latest AI SDK features
- 🏗️ [Architecture Guide](architecture.md) - System design and components
- 🚢 [Deployment Guide](DEPLOYMENT.md) - Deploy to production
- 📡 [API Reference](API.md) - Endpoint documentation

## Features
- **Multi-Model Support**: OpenAI (GPT-4.5, o1, o3), Anthropic (Claude 4, Sonnet 3.7), DeepSeek R1, and more
- **Advanced AI Capabilities**: Reasoning models, extended thinking, computer use, multi-step agents
- **Real-time Streaming**: Live game updates and move-by-move analysis
- **Structured Output**: Type-safe responses with Zod schemas
- **Production Ready**: Deployed on Vercel with edge functions and Supabase backend

## Getting Started

### Prerequisites
- Node.js 18+ or Python 3.9+
- Vercel account
- AI provider API keys (OpenAI, Anthropic, etc.)
- Supabase account (for database)

### Quick Installation

```bash
# Clone repository
git clone <repository-url>
cd tilts

# Install dependencies
pnpm install

# Install AI SDK
pnpm add ai@beta @ai-sdk/openai@beta @ai-sdk/anthropic@beta @ai-sdk/react@beta

# Configure environment
cp .env.example .env.local
# Add your API keys to .env.local
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Optional providers
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
MISTRAL_API_KEY=...
```

### Local Development
```bash
# Start development server
pnpm dev

# Or with Vercel CLI
vercel dev
```

### Deploy to Production
```bash
# Deploy to Vercel
vercel --prod

# Set environment variables in Vercel dashboard
# Settings → Environment Variables
```

## Project Structure
```
tilts/
├── api/                    # Vercel serverless functions (Python)
├── app/                    # Next.js app directory (if using)
├── components/             # React components
├── docs/                   # Documentation
│   ├── AI_SDK_QUICKSTART.md
│   ├── AI_IMPLEMENTATION_GUIDE.md
│   └── AI_SDK_MIGRATION.md
├── legacy/                 # Archived code
├── public/                 # Static assets
├── src/                    # Source code
├── supabase/              # Database migrations
└── packages/              # Shared packages
```

## AI SDK Integration

### Basic Example
```typescript
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const { text } = await generateText({
  model: openai('gpt-4.5-preview'),
  prompt: 'How do I win at Minesweeper?',
});
```

### Streaming Example
```typescript
import { streamText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const stream = await streamText({
  model: anthropic('claude-3-7-sonnet-20250219-v1:0'),
  messages: [{ role: 'user', content: 'Play Minesweeper' }],
  maxSteps: 50,
});

for await (const part of stream.textStream) {
  console.log(part);
}
```

### React Integration
```tsx
import { useChat } from '@ai-sdk/react';

export function GameUI() {
  const { messages, input, handleSubmit } = useChat();
  
  return (
    <form onSubmit={handleSubmit}>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button type="submit">Send</button>
    </form>
  );
}
```

## Available Models

### OpenAI
- `gpt-4.5-preview` - Latest GPT-4.5 model
- `gpt-4` - GPT-4 stable
- `o1` - Reasoning model
- `o3-mini` - Fast reasoning model
- `gpt-3.5-turbo` - Fast, cost-effective

### Anthropic
- `claude-4-sonnet-20250514` - Extended thinking
- `claude-3-7-sonnet-20250219-v1:0` - Latest Sonnet
- `claude-3-5-sonnet-20241022` - Computer use capable
- `claude-3-opus-20240229` - Most capable

### Others
- DeepSeek: `deepseek-reasoner` (R1)
- Groq: `llama-3.1-70b-versatile`
- Mistral: `mistral-large-latest`

## Documentation Index

### Core Guides
- [AI SDK Quick Start](AI_SDK_QUICKSTART.md) - Get started quickly
- [AI Implementation Guide](AI_IMPLEMENTATION_GUIDE.md) - Comprehensive patterns
- [AI SDK Migration](AI_SDK_MIGRATION.md) - Upgrade existing code

### Platform Docs
- [Architecture](architecture.md) - System design
- [API Reference](API.md) - Endpoint documentation
- [Deployment](DEPLOYMENT.md) - Production deployment
- [Database Setup](database-setup.md) - Supabase configuration

### Feature Guides
- [Evaluation System](evaluation.md) - Game evaluation framework
- [Function Calling](function-calling.md) - Tool use patterns
- [Real-time Updates](REALTIME_ARCHITECTURE.md) - Streaming architecture
- [Web Interface](web-interface.md) - Frontend documentation

### Operations
- [Debugging Guide](debugging.md) - Troubleshooting
- [Admin Guide](admin-guide.md) - Platform administration
- [Monitoring](user-behavior-monitoring.md) - Analytics and monitoring

## Support & Resources

### Vercel AI SDK
- [Official Docs](https://sdk.vercel.ai/docs)
- [GitHub](https://github.com/vercel/ai)
- [Examples](https://github.com/vercel/ai/tree/main/examples)
- [Discord](https://vercel.com/discord)

### Tilts Platform
- [GitHub Issues](https://github.com/your-org/tilts/issues)
- [Contributing Guide](../CONTRIBUTING.md)
- [Changelog](../CHANGELOG.md)

## Quick Commands

```bash
# Development
pnpm dev                    # Start dev server
pnpm build                  # Build for production
pnpm test                   # Run tests
pnpm lint                   # Run linter

# AI SDK
pnpm add ai@beta           # Update AI SDK
pnpm add @ai-sdk/[provider]@beta  # Add provider

# Deployment
vercel                     # Deploy to Vercel
vercel env pull            # Pull env vars
vercel logs                # View logs

# Database
pnpm supabase:migrate      # Run migrations
pnpm supabase:seed         # Seed database
```

## Contributing

See [Contributing Guide](../CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT License](../LICENSE)