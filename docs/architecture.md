# Tilts Architecture

## System Overview
Tilts is built as a serverless application on Vercel with Supabase for data persistence.

## Components

### Frontend
- **Location**: `/api/static/`
- **Technology**: Vanilla JavaScript with Dieter Rams-inspired design
- **Key Files**:
  - `index.html` - Main application
  - `app-rams.js` - Core application logic
  - `evaluate.html` - Standalone evaluation page

### Backend
- **Location**: `/api/`
- **Technology**: Python serverless functions
- **Key Endpoints**:
  - `/api/play` - Game execution
  - `/api/sessions` - Competition management
  - `/api/leaderboard` - Rankings
  - `/api/models` - AI model configuration

### Database
- **Provider**: Supabase (PostgreSQL)
- **URL**: https://mgkprogfsjmazekeyquq.supabase.co
- **Fallback**: JSON file storage when Supabase unavailable

### AI Integration
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku
- **Method**: Function calling for structured responses
- **Implementation**: Vercel AI SDK (required for all AI features)
- **Reference**: See `/docs/AI_IMPLEMENTATION_GUIDE.md` for implementation details

## Data Flow
1. User initiates evaluation via web UI
2. Frontend calls `/api/play` endpoint
3. Backend creates game instance in Supabase
4. Game runner executes with AI model
5. Results stored in database
6. Real-time updates via SSE
7. Leaderboard updates automatically

## Deployment Architecture
- **Hosting**: Vercel (serverless functions)
- **Database**: Supabase (managed PostgreSQL)
- **Static Assets**: Vercel CDN
- **Environment**: Production at https://tilts.vercel.app