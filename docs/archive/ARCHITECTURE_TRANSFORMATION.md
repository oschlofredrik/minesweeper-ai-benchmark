# Tilts to AI Competition Platform - Architecture Transformation

## Overview

This document outlines the transformation of Tilts from a Minesweeper-specific benchmark into a flexible, Kahoot-style AI competition platform that supports multiple games, dynamic scoring, and real-time multiplayer competitions.

## New Architecture Components

### 1. Game Plugin System (`src/games/base.py`)

The platform now uses a plugin-based architecture where each game implements a standard interface:

```python
class BaseGame(ABC):
    # Game metadata
    name: str                          # Unique identifier
    display_name: str                  # Human-readable name
    description: str                   # Brief description
    supported_modes: List[GameMode]    # Speed, accuracy, efficiency, etc.
    
    # Game functionality
    create_instance(config)            # Create new game instance
    get_scoring_components()           # Available scoring metrics
    get_ai_prompt_template()          # AI instruction template
    get_visualization_data(state)      # Frontend rendering data
```

Each game plugin provides:
- Game logic and rules
- State management
- Move validation
- Scoring calculations
- AI interaction format
- Visualization data

### 2. Flexible Scoring Framework (`src/scoring/framework.py`)

The new scoring system supports:

**Scoring Components**: Modular metrics that can be weighted differently
- Completion (binary success)
- Speed (time-based)
- Accuracy (correctness)
- Efficiency (optimal vs actual)
- Reasoning (explanation quality)
- Creativity (novelty)
- Game-specific metrics

**Scoring Profiles**: Pre-configured or custom weight combinations
- Speed Demon (70% speed, 20% completion, 10% accuracy)
- Perfectionist (50% accuracy, 30% efficiency, 20% reasoning)
- Efficiency Master (60% efficiency, 30% accuracy, 10% speed)
- Creative Challenge (40% creativity, 30% completion, 30% reasoning)
- Custom profiles with any weight distribution

**Competition Scoring**: Advanced rules for tournaments
- Bonus conditions (e.g., 20% bonus for perfect game)
- Penalty rules (e.g., -10% for timeout)
- Round-specific weightings

### 3. Session Management (`src/competition/session.py`)

Comprehensive session configuration supporting:

**Competition Formats**:
- Single Round: One game, quick match
- Multi-Round: Series of games/challenges
- Tournament: Elimination or bracket style
- Marathon: Continuous play until time limit
- Relay: Team-based competitions

**Session Features**:
- Dynamic round configuration
- Per-round game and scoring selection
- Player management and readiness tracking
- Real-time leaderboards
- Join codes for easy access
- Public/private sessions

### 4. Game Registry (`src/games/registry.py`)

Centralized game management:
- Auto-discovery of game plugins
- Dynamic game loading
- Mode-based filtering
- Metadata management
- Featured game curation

### 5. Generic Evaluation Engine (`src/evaluation/generic_engine.py`)

Game-agnostic evaluation system:
- Works with any game plugin
- Handles AI model interactions
- Tracks evaluation progress
- Streams real-time updates
- Calculates scores using profiles
- Manages session evaluations

## Migration Path

### Phase 1: Core Abstraction ✅
- [x] Create game plugin interface
- [x] Implement flexible scoring system
- [x] Build session management
- [x] Create game registry
- [x] Extract Minesweeper as plugin
- [x] Add generic evaluation engine

### Phase 2: Platform Expansion (Next Steps)
- [ ] Update database schema for multi-game support
- [ ] Convert API endpoints to be game-agnostic
- [ ] Update frontend for dynamic game rendering
- [ ] Add more game implementations
- [ ] Implement real-time WebSocket updates
- [ ] Create session lobby system

### Phase 3: Full Platform Features
- [ ] Tournament bracket system
- [ ] Team competition support
- [ ] Custom scoring formula editor
- [ ] Game creation tools
- [ ] Analytics dashboard
- [ ] Achievement system

## Example Games Implemented

### 1. Minesweeper (`src/games/implementations/minesweeper.py`)
The original game, now as a plugin with:
- Full game logic preserved
- Multiple difficulty levels
- All original scoring metrics
- Function calling support for AI

### 2. Number Puzzle (`src/games/implementations/number_puzzle.py`)
Simple demonstration game showing:
- Minimal game implementation
- Binary search strategy testing
- Efficiency scoring
- Different difficulty ranges

## Key Benefits of New Architecture

1. **Extensibility**: New games can be added without modifying core platform
2. **Flexibility**: Any scoring combination for any competition format
3. **Modularity**: Clean separation of concerns
4. **Scalability**: Ready for multiple concurrent sessions
5. **Customization**: Highly configurable competitions
6. **Educational**: Perfect for teaching AI strategies

## Usage Examples

### Quick Match
```python
from src.competition.session import SessionBuilder

session = SessionBuilder.create_quick_match(
    game_name="minesweeper",
    ai_model="gpt-4"
)
```

### Multi-Game Tournament
```python
session = SessionBuilder.create_tournament(
    games=["minesweeper", "number_puzzle", "sudoku"],
    rounds_per_game=2
)
```

### Custom Competition
```python
from src.competition.session import SessionConfig, RoundConfig
from src.scoring.framework import ScoringProfile, ScoringWeight

custom_session = SessionConfig(
    name="Logic Masters Tournament",
    format=CompetitionFormat.MULTI_ROUND,
    rounds=[
        RoundConfig(
            round_number=1,
            game_name="number_puzzle",
            game_config=GameConfig(difficulty="easy", mode=GameMode.SPEED),
            scoring_profile=StandardScoringProfiles.SPEED_DEMON,
            time_limit=60
        ),
        RoundConfig(
            round_number=2,
            game_name="minesweeper",
            game_config=GameConfig(difficulty="medium", mode=GameMode.ACCURACY),
            scoring_profile=StandardScoringProfiles.PERFECTIONIST,
            time_limit=300
        )
    ]
)
```

## Next Steps for Implementation

1. **Database Migration**: Update schema to support multiple games and sessions
2. **API Updates**: Convert endpoints from Minesweeper-specific to game-agnostic
3. **Frontend Refactor**: Create dynamic game rendering components
4. **WebSocket Integration**: Add real-time competition updates
5. **Game Library**: Implement 5-10 additional games
6. **Testing Suite**: Comprehensive tests for the new architecture

## Conclusion

The transformation creates a powerful, flexible platform for AI competitions that can:
- Host any type of logic/puzzle game
- Support various competition formats
- Provide fair, customizable scoring
- Scale to many concurrent sessions
- Enable educational and research use cases

The architecture is designed to grow with the platform, allowing easy addition of new games, scoring methods, and competition formats without disrupting existing functionality.