# Minesweeper AI Benchmark - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Interface                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Leaderboard │  │ Game Replay  │  │ Task Creation    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                         FastAPI Backend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Evaluation   │  │   Results    │  │    Task API     │  │
│  │   Endpoint   │  │     API      │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      Core Platform Layer                     │
│                                                              │
│  ┌────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │   Game     │  │     Model      │  │   Evaluation    │  │
│  │  Engine    │  │   Interface    │  │     Engine      │  │
│  │            │  │                │  │                 │  │
│  │ • Board    │  │ • OpenAI       │  │ • Metrics       │  │
│  │ • Solver   │  │ • Anthropic    │  │ • Scoring       │  │
│  │ • States   │  │ • Local Models │  │ • Analysis      │  │
│  └────────────┘  └────────────────┘  └─────────────────┘  │
│                                                              │
│  ┌────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │    Task    │  │  Communication │  │     Storage     │  │
│  │ Repository │  │     Module     │  │   (Database)    │  │
│  └────────────┘  └────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                          CLI Tool                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Evaluate   │  │    Create    │  │     Compare     │  │
│  │   Command    │  │    Task      │  │     Models      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Game Engine
**Purpose**: Manages Minesweeper game logic and state

**Key Classes**:
- `MinesweeperBoard`: Board representation and mine placement
- `MinesweeperGame`: Game flow and move validation  
- `MinesweeperSolver`: Algorithmic solver for validation

**Interfaces**:
```python
class GameEngine:
    def reset(self) -> GameState
    def step(self, action: Action) -> Tuple[GameState, Reward, Done]
    def render_text(self) -> str
    def get_valid_actions(self) -> List[Action]
```

### 2. Model Interface
**Purpose**: Unified interface for all LLM interactions

**Adapters**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- HuggingFace (local models)

**Key Features**:
- Async generation
- Rate limiting
- Error handling
- Response parsing

### 3. Evaluation Engine
**Purpose**: Orchestrates model evaluation and metrics

**Process Flow**:
1. Load tasks from repository
2. Initialize model interface
3. For each task:
   - Reset game environment
   - Loop: Get model action → Execute → Update state
   - Calculate metrics
   - Store results

**Metrics Tracked**:
- Win rate
- Valid move percentage
- Mine identification accuracy
- Average moves to completion
- Reasoning quality score

### 4. Task System
**Purpose**: Manages benchmark tasks and scenarios

**Task Types**:
- **Static**: Single-turn puzzles ("What's the next move?")
- **Interactive**: Full game scenarios
- **Custom**: User-created challenges

**Schema**:
```json
{
  "id": "task_001",
  "type": "interactive",
  "difficulty": "expert",
  "board_config": {
    "rows": 16,
    "cols": 30,
    "mines": 99,
    "seed": 42
  },
  "metadata": {
    "created_by": "system",
    "tags": ["expert", "deterministic"]
  }
}
```

### 5. Storage Layer
**Purpose**: Persistent storage for all data

**Tables**:
- `models`: Registered models and configurations
- `tasks`: Task definitions and solutions
- `evaluations`: Run results and metrics
- `transcripts`: Detailed game logs

### 6. Communication Module
**Purpose**: Handles model prompting and response parsing

**Responsibilities**:
- Format board state for model
- Parse model actions
- Maintain conversation context
- Handle structured outputs

## Data Flow

### Evaluation Flow
```
1. User Request
   └─> CLI/API: "Evaluate GPT-4 on expert boards"
   
2. Task Loading
   └─> Repository: Fetch 100 expert-level tasks
   
3. Model Initialization
   └─> Interface: Connect to OpenAI API
   
4. Game Loop (per task)
   ├─> Game Engine: Initialize board
   ├─> Communication: Format prompt
   ├─> Model: Generate action
   ├─> Parser: Extract move
   ├─> Game Engine: Execute move
   └─> Repeat until game ends
   
5. Metrics Calculation
   └─> Evaluation: Compute all metrics
   
6. Storage
   └─> Database: Save results and transcript
   
7. Response
   └─> User: Display results/update leaderboard
```

## Key Design Patterns

### 1. Strategy Pattern
For model interfaces - each model type implements the same interface differently

### 2. Factory Pattern
For creating game environments and tasks

### 3. Observer Pattern
For game state updates and event handling

### 4. Repository Pattern
For data access abstraction

### 5. Adapter Pattern
For integrating different model APIs

## Configuration Management

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@localhost/minesweeper

# Application
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
```

### Config Structure
```python
class Config(BaseSettings):
    # API Configuration
    openai_api_key: str
    anthropic_api_key: str
    
    # Database
    database_url: str
    
    # Game Settings
    default_board_size: Tuple[int, int] = (16, 30)
    default_mine_count: int = 99
    
    # Evaluation
    max_moves_per_game: int = 500
    evaluation_timeout: int = 300
    
    class Config:
        env_file = ".env"
```

## Extensibility Points

### 1. New Games
Implement `BaseGame` interface:
```python
class BaseGame(ABC):
    @abstractmethod
    def reset(self) -> GameState
    
    @abstractmethod  
    def step(self, action: Action) -> StepResult
    
    @abstractmethod
    def render(self) -> str
```

### 2. New Models
Implement `BaseModel` interface:
```python
class NewModelAdapter(BaseModel):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Custom implementation
        pass
```

### 3. New Metrics
Add to evaluation engine:
```python
def calculate_custom_metric(transcript: GameTranscript) -> float:
    # Custom metric logic
    pass
```

### 4. New Task Types
Extend task schema and add handler:
```python
class CustomTaskType(BaseTask):
    def generate_prompt(self) -> str:
        pass
    
    def evaluate_response(self, response: str) -> Result:
        pass
```

## Performance Considerations

### 1. Caching
- Model responses for development
- Compiled regex patterns
- Database query results

### 2. Async Operations
- All model calls are async
- Database operations use async SQLAlchemy
- Concurrent task evaluation

### 3. Resource Management
- Connection pooling for database
- Rate limiting for APIs
- Memory limits for local models

### 4. Scalability
- Horizontal scaling via task queue
- Read replicas for database
- CDN for static assets

## Security Measures

### 1. API Security
- Authentication tokens
- Rate limiting
- Input validation

### 2. Data Protection
- Encrypted API keys
- Sanitized user inputs
- SQL injection prevention

### 3. Model Security
- Prompt injection protection
- Output validation
- Resource limits

## Monitoring & Observability

### 1. Metrics
- API response times
- Model evaluation duration
- Error rates
- Resource usage

### 2. Logging
- Structured JSON logs
- Correlation IDs
- Error tracking

### 3. Tracing
- Distributed tracing for requests
- Performance profiling
- Bottleneck identification

## Development Workflow

### 1. Local Development
```bash
# Start services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload

# Run CLI
python -m src.cli evaluate --model gpt-4
```

### 2. Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/
```

### 3. Deployment
```bash
# Build Docker image
docker build -t minesweeper-benchmark .

# Deploy to Kubernetes
kubectl apply -f k8s/

# Run migrations
kubectl exec -it deploy/api -- alembic upgrade head
```

## Success Criteria

1. **Functional**: Can evaluate multiple models on Minesweeper
2. **Performant**: <30s per game evaluation
3. **Scalable**: Handle 1000+ concurrent evaluations
4. **Extensible**: Easy to add new games/models
5. **Reliable**: 99.9% uptime
6. **Usable**: Clear documentation and intuitive interface