# Tilts Platform Documentation

## Overview
Tilts is a comprehensive AI evaluation platform for logic-based games, deployed on Vercel with Supabase backend.

## Quick Links
- [Architecture Guide](ARCHITECTURE.md) - System design and components
- [Deployment Guide](DEPLOYMENT.md) - How to deploy to production
- [API Reference](API.md) - Endpoint documentation

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Vercel CLI
- Supabase account

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://mgkprogfsjmazekeyquq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Local Development
```bash
# Install dependencies
npm install
pip install -r api/requirements.txt

# Run locally
vercel dev
```

### Deployment
```bash
# Deploy to Vercel
vercel --prod
```

## Project Structure
```
tilts/
├── api/              # Vercel serverless functions
├── docs/             # Documentation
├── legacy/           # Archived code
└── supabase/         # Database migrations
```