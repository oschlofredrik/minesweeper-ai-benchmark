# Technical Debt Documentation

Last Updated: July 24, 2025

## Overview
This document tracks known technical debt in the Tilts platform (formerly Minesweeper AI Benchmark). The platform evolved from a single-game benchmark to a multi-game competition platform, resulting in some architectural inconsistencies.

## Database Schema Issues

### 0. Missing games_registry Table
**Impact**: High  
**Location**: `/api/games` endpoint  
**Description**: The `games_registry` table is referenced in code but doesn't exist in the database, causing 500 errors on the games list endpoint.
**Workaround**: Games are still registered in memory via the registry system.
**Fix**: Either create the table or remove database queries from the endpoint.

### 1. Minesweeper-Specific Fields in Core Tables
**Impact**: Medium  
**Location**: Database schema, models  
**Description**: The database schema still contains Minesweeper-specific fields in core tables:
- `games` table has columns like `mines_found`, `cells_revealed` 
- Leaderboard entries have Minesweeper-centric metrics
- These fields are null/unused for other game types

**Potential Solution**: 
- Create a polymorphic game_data JSON column for game-specific data
- Or create separate tables for each game type's specific data
- Migrate existing data to new structure

### 2. Missing Indexes
**Impact**: Low (current volume)  
**Location**: Database  
**Description**: Several frequently queried columns lack indexes:
- `games.model_name` (used in leaderboard queries)
- `games.created_at` (used in sorting)
- `leaderboard_entries.game_name` (used in filtering)

## Architecture Inconsistencies

### 1. Game Registration System
**Impact**: Low  
**Location**: `src/games/registry.py`  
**Description**: Games are registered in multiple places:
- `register_builtin_games()` in registry
- Plugin system can also register games
- Some endpoints manually check for game existence

**Potential Solution**: Centralize game registration on startup

### 2. Mixed Async/Sync Patterns
**Impact**: Medium  
**Location**: Throughout codebase  
**Description**: 
- Some database operations use sync SQLAlchemy
- API endpoints are async but sometimes call sync functions
- Could impact performance under load

### 3. Event Streaming Architecture
**Impact**: Low  
**Location**: `src/api/event_streaming.py`  
**Description**:
- Uses in-memory event storage
- Will lose events on restart
- No persistence or replay capability
- Single server only (no horizontal scaling)

## Code Organization Issues

### 1. Evaluation Module Complexity
**Impact**: Medium  
**Location**: `src/evaluation/`  
**Description**: The evaluation module has overlapping responsibilities:
- `streaming_runner.py` and `runner.py` have similar functionality
- `engine.py` and `advanced_metrics.py` duplicate some logic
- Episode logging spread across multiple files

### 2. Model Interface Inconsistency
**Impact**: Low  
**Location**: `src/models/`  
**Description**:
- OpenAI and Anthropic models have different error handling
- Function calling implementation differs between providers
- Retry logic is inconsistent

## Platform Evolution Artifacts

### 1. Naming Inconsistencies
**Impact**: Low  
**Location**: Throughout  
**Description**:
- Repository still named "minesweeper-benchmark"
- Some modules reference "minesweeper" when they're generic
- MineBench references in docs when platform supports multiple games

### 2. Frontend Coupling
**Impact**: Medium  
**Location**: `src/api/static/`  
**Description**:
- Frontend has hardcoded references to specific games
- Game visualization is tightly coupled to Tilts
- Adding new games requires frontend changes

### 3. Competition System Design
**Impact**: Medium  
**Location**: `src/api/session_endpoints.py`, `competition_runner.py`  
**Description**:
- In-memory session storage (loses data on restart)
- No session persistence
- Can't resume interrupted competitions
- Single-server only design

## Performance Concerns

### 1. N+1 Query Problems
**Impact**: Medium  
**Location**: API endpoints  
**Description**:
- Leaderboard endpoint loads related data inefficiently
- Game history endpoints don't use eager loading
- Could impact performance with more data

### 2. Large Result Sets
**Impact**: Low (current volume)  
**Location**: API endpoints  
**Description**:
- No pagination on some endpoints returning lists
- Full game transcripts loaded into memory
- Could cause issues with many games

## Security & Configuration

### 1. API Key Management
**Impact**: Medium  
**Location**: Configuration  
**Description**:
- API keys stored in environment variables
- No key rotation mechanism
- No per-user API key support

### 2. Admin Interface Security
**Impact**: Medium  
**Location**: `/admin` endpoints  
**Description**:
- Basic auth implementation
- No role-based access control
- All admin users have full access

## Testing Gaps

### 1. Integration Test Coverage
**Impact**: Medium  
**Description**:
- Competition system lacks comprehensive tests
- Event streaming not well tested
- Cross-game compatibility tests missing

### 2. Performance Testing
**Impact**: Low  
**Description**:
- No load testing for concurrent games
- No benchmarks for large competitions
- Database query performance not measured

## Documentation Debt

### 1. API Documentation
**Impact**: Low  
**Description**:
- Some new endpoints lack OpenAPI specs
- Competition API not fully documented
- WebSocket/SSE events not documented

### 2. Deployment Documentation
**Impact**: Medium  
**Description**:
- Render deployment specifics not documented
- Scaling considerations not addressed
- Backup/restore procedures missing

## Recommended Priorities

### High Priority:
1. Fix database schema to support multiple game types properly
2. Add session persistence for competitions
3. Improve admin interface security

### Medium Priority:
1. Standardize async patterns throughout
2. Add pagination to list endpoints
3. Improve error handling consistency
4. Add integration tests for competition system

### Low Priority:
1. Rename repository to reflect multi-game nature
2. Add database indexes
3. Consolidate evaluation modules
4. Update documentation

## Notes
- Most of these issues work fine for current usage levels
- Prioritize based on actual user needs and growth
- Many "issues" are acceptable tradeoffs for a research platform
- Focus fixes on items that block new features or cause user issues