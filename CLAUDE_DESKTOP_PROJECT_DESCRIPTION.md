# Tilts - AI Competition Platform

## Project Overview

Tilts is a flexible, game-agnostic AI competition platform that enables real-time multiplayer AI competitions similar to Kahoot, but designed specifically for evaluating and competing with Large Language Models (LLMs). The platform was originally built as a Minesweeper AI benchmark but has been transformed into a comprehensive system supporting multiple logic-based games.

## Core Concept

Think of Tilts as "Kahoot for AI" - users can host competitions where participants write prompts to guide AI models through various games. Unlike Kahoot's synchronous quiz format, Tilts handles the asynchronous nature of AI evaluation while maintaining competitive engagement through lobbies, real-time updates, and showcase features.

## Key Features

### 1. **Multi-Game Support**
- Plugin architecture allows easy addition of new games
- Currently supports: Minesweeper, Sudoku, Number Puzzle
- Each game has configurable difficulty levels and modes
- Games implement a standard interface for consistent evaluation

### 2. **Competition System**
- **Session-based competitions** with multiple rounds
- **Flexible formats**: Single round, Best-of-3, Tournament
- **Join codes** like "PLAY123" for easy access
- **Separate join portal** at join.tilts.com (Kahoot.it style)

### 3. **Asynchronous Game Flow**
- Handles AI evaluation delays (30s-5min per move)
- Players write prompts while others are being evaluated
- Real-time queue system with priority handling
- Engagement activities during wait times

### 4. **Prompt Engineering Focus**
- **Prompt templates** and libraries
- **Quality analysis** and suggestions
- **Shared prompt repository** with ratings
- **Version control** for prompt iterations

### 5. **Real-Time Features**
- WebSocket connections for live updates
- Event streaming for move-by-move details
- Spectator mode with multiple viewing angles
- Between-round showcases with highlights

### 6. **Evaluation & Scoring**
- **Flexible scoring framework** with customizable weights
- **Multiple metrics**: Win rate, efficiency, strategy quality
- **LLM-based reasoning judge** for explanation quality
- **Statistical significance testing** (Wilson intervals)

## Technical Architecture

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL (with file-based fallback)
- **Deployment**: Render.com with auto-scaling
- **APIs**: OpenAI and Anthropic native function calling

### Frontend
- **Design**: Minimalist Dieter Rams aesthetic
- **Framework**: Vanilla JavaScript (intentionally simple)
- **Real-time**: WebSockets for live updates
- **Mobile**: Responsive design for prompt writing

### Infrastructure
- **Main Platform**: tilts.com (formerly minesweeper-ai-benchmark.onrender.com)
- **Join Service**: join.tilts.com (separate microservice)
- **Monitoring**: Structured JSON logging with rotation
- **CI/CD**: GitHub Actions with auto-deployment

## Game Plugin System

Games are implemented as plugins following a standard interface:

```python
class BaseGame(ABC):
    - create_instance() -> GameInstance
    - get_default_config() -> GameConfig
    - validate_config() -> bool

class GameInstance(ABC):
    - make_move() -> MoveResult
    - get_state() -> GameState
    - is_game_over() -> bool
```

This allows adding new games without modifying core platform code.

## User Journeys

### 1. **Competition Host**
1. Creates session with game selection and format
2. Receives join code to share
3. Monitors lobby as players join
4. Starts competition when ready
5. Views real-time results and showcases

### 2. **Player**
1. Joins via code at join.tilts.com
2. Enters lobby with practice activities
3. Writes prompts for each round
4. Sees real-time evaluation progress
5. Reviews performance and learns from others

### 3. **Spectator**
1. Joins session with view-only access
2. Watches multiple games simultaneously
3. Sees move-by-move reasoning
4. Can analyze different strategies

## Research Applications

### 1. **AI Capability Assessment**
- Benchmark logical reasoning across models
- Compare prompt sensitivity between models
- Identify failure modes in game scenarios
- Track improvement over model versions

### 2. **Prompt Engineering Research**
- A/B test different prompting strategies
- Analyze which instructions work best
- Build corpus of effective prompts
- Study prompt transferability between models

### 3. **Human-AI Collaboration**
- How humans guide AI through complex tasks
- Optimal prompt complexity vs performance
- Learning curves for prompt writing
- Collective intelligence in competitions

### 4. **Educational Use Cases**
- Teaching logical reasoning concepts
- Demonstrating AI capabilities/limitations
- Prompt engineering workshops
- AI literacy through gameplay

## Current State

The platform is fully deployed and operational with:
- Complete game engine and evaluation system
- Real-time competition infrastructure
- Comprehensive API with documentation
- Production deployment on Render
- Active development of new features

## Future Directions

### Platform Features
- More games (Chess, Go, Logic Puzzles)
- Tournament management system
- Team competitions
- Achievement/progression system
- Mobile app for prompt writing

### Research Tools
- Automated prompt optimization
- Cross-model prompt translation
- Performance prediction models
- Detailed analytics dashboard
- Dataset export for research

### Community Features
- Public prompt marketplace
- Competition replays with commentary
- Leaderboards by game/model/timeframe
- Social features for teams/clubs

## Key Insights

1. **Asynchronous Design**: Unlike traditional real-time games, AI competitions must handle evaluation delays while maintaining engagement

2. **Prompt Quality Matters**: The platform reveals how prompt engineering skill significantly impacts AI performance

3. **Model Differences**: Different models excel at different games and respond differently to prompting strategies

4. **Learning Through Competition**: Competitive format motivates users to improve their prompt engineering skills

5. **Flexible Architecture**: Plugin system allows easy expansion while maintaining consistent evaluation

## Related Documentation

- **CLAUDE.md**: Memory and context for AI assistants
- **README.md**: Technical setup and deployment
- **ARCHITECTURE.md**: System design decisions
- **TRANSFORM_NOTES.md**: Journey from Minesweeper to Tilts

## Research Questions to Explore

1. How do different prompt structures affect AI game performance?
2. Can we predict AI success based on prompt characteristics?
3. What makes some games harder for AI than others?
4. How do competitive dynamics change prompt writing behavior?
5. Can collaborative prompt writing outperform individual efforts?
6. What prompt patterns transfer between different games?
7. How does model size correlate with prompt sensitivity?
8. Can we automatically generate optimal prompts for new games?

## Access and Resources

- **Production**: https://tilts.com
- **GitHub**: https://github.com/oschlofredrik/tilts
- **Original**: Evolved from Minesweeper AI Benchmark
- **Contact**: Built by Fredrik (GitHub: oschlofredrik)

This platform bridges the gap between AI benchmarking and interactive competition, creating a unique environment for both research and engagement with AI capabilities.