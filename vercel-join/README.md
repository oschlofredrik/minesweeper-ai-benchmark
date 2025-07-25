# Tilts Join Service

Minimal join service for Tilts platform - Kahoot-style PIN entry.

## Deployment

This is meant to be deployed as a separate Vercel project:

1. Create new Vercel project pointing to the `vercel-join` directory
2. Deploy with domain `join-tilts.vercel.app` or custom domain `join.tilts.com`

## Features

- Clean, minimal UI optimized for mobile
- Auto-uppercase PIN entry
- 4-character PIN validation
- Redirects to main platform with join code

## Local Development

```bash
cd vercel-join
vercel dev
```

Visit http://localhost:3000