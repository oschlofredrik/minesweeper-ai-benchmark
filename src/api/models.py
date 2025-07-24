"""Pydantic models for API responses."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for a model."""
    rank: int
    model_id: str
    model_name: str
    global_score: float
    ms_s_score: float
    ms_i_score: float
    win_rate: float
    accuracy: float
    coverage: float
    reasoning_score: float
    num_games: int
    last_updated: datetime
    statistical_significance: Optional[Dict[str, Any]] = None


class ModelResult(BaseModel):
    """Detailed results for a single model."""
    model_id: str
    model_name: str
    provider: str
    evaluation_date: datetime
    num_tasks: int
    metrics: Dict[str, float]
    per_task_type_metrics: Dict[str, Dict[str, float]]
    confidence_intervals: Dict[str, tuple]
    prompt_variant: str
    eval_spec_version: str = "v1.0"


class TaskInfo(BaseModel):
    """Information about a benchmark task."""
    task_uid: str
    task_type: str
    difficulty: str
    description: str
    created_at: datetime


class GameReplay(BaseModel):
    """Game replay data."""
    game_id: str
    model_name: str
    task_uid: str
    moves: List[Dict[str, Any]]
    final_status: str
    board_config: Dict[str, int]
    duration_seconds: float


class EvaluationRequest(BaseModel):
    """Request to evaluate models."""
    models: List[str]
    num_games: int = 10
    task_type: str = "interactive"
    difficulty: str = "expert"


class ComparisonResult(BaseModel):
    """Result of model comparison."""
    models: List[str]
    comparison_id: str
    message: str


class GameInfo(BaseModel):
    """Information about a game."""
    name: str
    display_name: str
    description: str
    supported_modes: List[str]
    is_active: bool
    player_count: int


class GameListResponse(BaseModel):
    """Response for listing games."""
    games: List[GameInfo]
    total: int


class GamePlayRequest(BaseModel):
    """Request to play a game."""
    player_id: str
    ai_model: str
    difficulty: str = "medium"
    mode: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None
    time_limit: Optional[int] = None
    session_id: Optional[str] = None
    round_number: Optional[int] = None


class GamePlayResponse(BaseModel):
    """Response after starting a game."""
    game_id: int
    instance_id: str
    initial_state: Dict[str, Any]
    visualization_data: Dict[str, Any]