"""Database models and utilities for persistent storage."""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import NullPool
import os

Base = declarative_base()

class Game(Base):
    """Store game sessions and their states."""
    __tablename__ = 'games'
    
    id = Column(String, primary_key=True)  # game_id
    model_provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    mines = Column(Integer, nullable=False)
    
    # Game state
    initial_board = Column(JSON, nullable=False)  # Store the initial mine positions
    final_board = Column(JSON, nullable=True)  # Final revealed board state
    moves = Column(JSON, nullable=False)  # List of all moves made
    
    # Results
    won = Column(Boolean, nullable=False)
    num_moves = Column(Integer, nullable=False)
    valid_moves = Column(Integer, nullable=False)
    invalid_moves = Column(Integer, nullable=False)
    flags_placed = Column(Integer, nullable=False)
    cells_revealed = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="game", cascade="all, delete-orphan")


class Evaluation(Base):
    """Store evaluation results for games."""
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey('games.id'), nullable=False)
    
    # Metrics
    win_rate = Column(Float, nullable=False)
    valid_move_rate = Column(Float, nullable=False)
    mine_identification_precision = Column(Float, nullable=False)
    mine_identification_recall = Column(Float, nullable=False)
    board_coverage = Column(Float, nullable=False)
    efficiency_score = Column(Float, nullable=False)
    strategic_score = Column(Float, nullable=False)
    reasoning_score = Column(Float, nullable=True)
    composite_score = Column(Float, nullable=False)
    
    # Additional data
    total_time_seconds = Column(Float, nullable=True)
    reasoning_analysis = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="evaluations")


class Task(Base):
    """Store generated benchmark tasks."""
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)  # task_id
    difficulty = Column(String, nullable=False)
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    mines = Column(Integer, nullable=False)
    
    # Board configuration
    mine_positions = Column(JSON, nullable=False)
    initial_state = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    used_count = Column(Integer, default=0)
    
    # Statistics
    avg_win_rate = Column(Float, nullable=True)
    avg_moves = Column(Float, nullable=True)
    
    
class PromptTemplate(Base):
    """Store prompt templates for different models."""
    __tablename__ = 'prompt_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    model_provider = Column(String, nullable=True)  # Optional, for model-specific prompts
    
    # Template content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    
    # Performance metrics
    avg_win_rate = Column(Float, nullable=True)
    avg_valid_move_rate = Column(Float, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class LeaderboardEntry(Base):
    """Cached leaderboard entries for performance."""
    __tablename__ = 'leaderboard_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    
    # Aggregate metrics
    total_games = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    valid_move_rate = Column(Float, nullable=False)
    mine_precision = Column(Float, nullable=False)
    mine_recall = Column(Float, nullable=False)
    board_coverage = Column(Float, nullable=False)
    efficiency_score = Column(Float, nullable=False)
    strategic_score = Column(Float, nullable=False)
    reasoning_score = Column(Float, nullable=True)
    global_score = Column(Float, nullable=False)
    
    # Confidence intervals
    win_rate_ci_lower = Column(Float, nullable=True)
    win_rate_ci_upper = Column(Float, nullable=True)
    
    # Last update
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database connection management
_engine = None
_SessionLocal = None

def get_database_url() -> str:
    """Get database URL from environment or use SQLite for local development."""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Render uses postgres:// but SQLAlchemy needs postgresql+psycopg2://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return database_url
    else:
        # Use SQLite for local development
        return 'sqlite:///./minesweeper_benchmark.db'


def init_db():
    """Initialize database connection."""
    global _engine, _SessionLocal
    
    database_url = get_database_url()
    
    if 'sqlite' in database_url:
        # SQLite doesn't support async, use sync driver
        database_url = database_url.replace('sqlite+aiosqlite', 'sqlite')
        _engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        # PostgreSQL with connection pooling disabled for serverless
        _engine = create_engine(database_url, poolclass=NullPool)
    
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=_engine)
    
    return _engine


def get_db() -> Session:
    """Get database session."""
    if _SessionLocal is None:
        init_db()
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions for data conversion
def game_to_dict(game: Game) -> Dict[str, Any]:
    """Convert Game model to dictionary."""
    return {
        'game_id': game.id,
        'model': {
            'provider': game.model_provider,
            'name': game.model_name
        },
        'difficulty': game.difficulty,
        'board_size': {
            'rows': game.rows,
            'cols': game.cols,
            'mines': game.mines
        },
        'moves': game.moves,
        'results': {
            'won': game.won,
            'num_moves': game.num_moves,
            'valid_moves': game.valid_moves,
            'invalid_moves': game.invalid_moves,
            'flags_placed': game.flags_placed,
            'cells_revealed': game.cells_revealed
        },
        'created_at': game.created_at.isoformat() if game.created_at else None,
        'completed_at': game.completed_at.isoformat() if game.completed_at else None
    }


def evaluation_to_dict(evaluation: Evaluation) -> Dict[str, Any]:
    """Convert Evaluation model to dictionary."""
    return {
        'game_id': evaluation.game_id,
        'metrics': {
            'win_rate': evaluation.win_rate,
            'valid_move_rate': evaluation.valid_move_rate,
            'mine_identification_precision': evaluation.mine_identification_precision,
            'mine_identification_recall': evaluation.mine_identification_recall,
            'board_coverage': evaluation.board_coverage,
            'efficiency_score': evaluation.efficiency_score,
            'strategic_score': evaluation.strategic_score,
            'reasoning_score': evaluation.reasoning_score,
            'composite_score': evaluation.composite_score
        },
        'total_time_seconds': evaluation.total_time_seconds,
        'reasoning_analysis': evaluation.reasoning_analysis,
        'created_at': evaluation.created_at.isoformat() if evaluation.created_at else None
    }