# Vercel Deployment Guide

## Prerequisites

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Create a Vercel account at https://vercel.com

## Environment Variables

You'll need to set these environment variables in Vercel:

- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key  
- `DATABASE_URL` - PostgreSQL connection string (or use SQLite)
- `SECRET_KEY` - A random secret key for sessions

## Deployment Steps

1. **Login to Vercel**:
```bash
vercel login
```

2. **Deploy**:
```bash
vercel
```

When prompted:
- Set up and deploy: Y
- Which scope: Select your account
- Link to existing project? N  
- Project name: minesweeper-benchmark (or your preferred name)
- In which directory: . (current)
- Override settings? N

3. **Set Environment Variables**:
```bash
# Set each environment variable
vercel env add OPENAI_API_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add DATABASE_URL
vercel env add SECRET_KEY
```

4. **Deploy to Production**:
```bash
vercel --prod
```

## Post-Deployment

1. Your app will be available at: `https://your-project-name.vercel.app`

2. The API endpoints will be at:
   - `/docs` - API documentation
   - `/health` - Health check
   - `/api/leaderboard` - Leaderboard data
   - `/` - Main web interface

## Database Considerations

For Vercel deployment, you'll need an external database:

1. **PostgreSQL** (Recommended):
   - Use Vercel Postgres, Supabase, or Neon
   - Update DATABASE_URL with connection string

2. **SQLite** (Development only):
   - Limited to read-only or temporary data
   - Not recommended for production

## Limitations

- Vercel has a 10MB function size limit (we've configured 15MB max)
- API routes have a 30-second timeout
- Static files are served from `/src/api/static/`
- Large file operations may need adjustment

## Troubleshooting

1. **Module Import Errors**: 
   - Check that all dependencies are in `requirements-vercel.txt`
   - Ensure paths in `api/index.py` are correct

2. **Static Files Not Loading**:
   - Verify routes in `vercel.json`
   - Check file paths match deployment structure

3. **Database Connection Issues**:
   - Verify DATABASE_URL is set correctly
   - Check database is accessible from Vercel's network

## Local Testing

Test the Vercel build locally:
```bash
vercel dev
```

This will simulate the Vercel environment on your machine.