"""Database models for multi-game support."""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class GameRegistry(Base):
    """Registry of available games."""
    __tablename__ = 'games_registry'
    
    game_name = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    supported_modes = Column(JSON, nullable=False)
    scoring_components = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    config = Column(JSON, nullable=True)
    
    # Relationships
    rounds = relationship("SessionRound", back_populates="game")
    prompts = relationship("PromptLibrary", back_populates="game")


class CompetitionSession(Base):
    """A competition session."""
    __tablename__ = 'competition_sessions'
    
    session_id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    format = Column(String(50), nullable=False)  # single_round, multi_round, tournament, marathon
    join_code = Column(String(10), nullable=False, unique=True, index=True)
    is_public = Column(Boolean, default=True)
    max_players = Column(Integer, default=50)
    min_players = Column(Integer, default=1)
    creator_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default='waiting', index=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    config = Column(JSON, nullable=False)
    
    # Relationships
    rounds = relationship("SessionRound", back_populates="session", cascade="all, delete-orphan")
    players = relationship("SessionPlayer", back_populates="session", cascade="all, delete-orphan")
    spectators = relationship("SpectatorSession", back_populates="session", cascade="all, delete-orphan")


class SessionRound(Base):
    """A round in a competition session."""
    __tablename__ = 'session_rounds'
    
    round_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey('competition_sessions.session_id'), nullable=False)
    round_number = Column(Integer, nullable=False)
    game_name = Column(String(50), ForeignKey('games_registry.game_name'), nullable=False)
    game_config = Column(JSON, nullable=False)
    scoring_profile = Column(JSON, nullable=False)
    time_limit = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('session_id', 'round_number'),
    )
    
    # Relationships
    session = relationship("CompetitionSession", back_populates="rounds")
    game = relationship("GameRegistry", back_populates="rounds")


class SessionPlayer(Base):
    """A player in a competition session."""
    __tablename__ = 'session_players'
    
    session_id = Column(String(36), ForeignKey('competition_sessions.session_id'), primary_key=True)
    player_id = Column(String(36), primary_key=True)
    player_name = Column(String(100), nullable=False)
    ai_model = Column(String(50), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())
    is_ready = Column(Boolean, default=False)
    warmup_score = Column(Float, default=0.0)
    final_rank = Column(Integer, nullable=True)
    total_score = Column(Float, default=0.0)
    
    # Relationships
    session = relationship("CompetitionSession", back_populates="players")


class PromptLibrary(Base):
    """Saved prompts in the library."""
    __tablename__ = 'prompt_library'
    
    prompt_id = Column(String(36), primary_key=True)
    owner_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    game_name = Column(String(50), ForeignKey('games_registry.game_name'), nullable=False, index=True)
    template_id = Column(String(36), nullable=True)
    visibility = Column(String(20), default='private', index=True)
    tags = Column(JSON, nullable=True)
    version = Column(Integer, default=1)
    parent_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    usage_count = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    avg_score = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    likes = Column(Integer, default=0)
    prompt_metadata = Column('metadata', JSON, nullable=True)
    
    # Relationships
    game = relationship("GameRegistry", back_populates="prompts")


class SpectatorSession(Base):
    """A spectator viewing a session."""
    __tablename__ = 'spectator_sessions'
    
    spectator_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey('competition_sessions.session_id'), nullable=False)
    name = Column(String(100), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())
    view_mode = Column(String(20), default='overview')
    prediction_score = Column(Integer, default=0)
    watch_time = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    
    # Relationships
    session = relationship("CompetitionSession", back_populates="spectators")


class ScoringProfile(Base):
    """Scoring profiles for competitions."""
    __tablename__ = 'scoring_profiles'
    
    profile_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String, nullable=True)
    weights = Column(JSON, nullable=False)
    is_preset = Column(Boolean, default=False)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PlayerProfile(Base):
    """Player profiles and statistics."""
    __tablename__ = 'player_profiles'
    
    player_id = Column(String(36), primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, nullable=True)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    skill_ratings = Column(JSON, nullable=True)  # {game_name: rating}
    achievements = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)
    stats = Column(JSON, nullable=True)


class QueueItem(Base):
    """Items in the evaluation queue."""
    __tablename__ = 'queue_items'
    
    item_id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    game_name = Column(String(50), nullable=False)
    prompt = Column(String, nullable=False)
    priority = Column(Integer, default=2)
    status = Column(String(20), default='queued', index=True)
    submitted_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String(36), nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_session_round', 'session_id', 'round_number'),
    )


# Updated Game model to support multi-game
class Game(Base):
    """Individual game instances."""
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    game_name = Column(String(50), nullable=False, default='minesweeper', index=True)
    session_id = Column(String(36), nullable=True)
    round_number = Column(Integer, nullable=True)
    prompt_id = Column(String(36), nullable=True)
    player_id = Column(String(36), nullable=True)
    ai_model = Column(String(50), nullable=True)
    job_id = Column(String, nullable=True)
    task_id = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    model_provider = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    board_config = Column(JSON, nullable=True)
    moves = Column(JSON, nullable=True)
    outcome = Column(JSON, nullable=True)
    full_transcript = Column(JSON, nullable=True)
    evaluation_time = Column(Float, nullable=True)
    score_components = Column(JSON, nullable=True)
    final_score = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_session_round', 'session_id', 'round_number'),
    )


# Updated LeaderboardEntry to support multiple games
class LeaderboardEntry(Base):
    """Leaderboard entries per game."""
    __tablename__ = 'leaderboard_entries'
    
    id = Column(Integer, primary_key=True)
    game_name = Column(String(50), nullable=False, default='minesweeper')
    model_name = Column(String, nullable=False)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_score = Column(Float, default=0.0)
    best_score = Column(Float, default=0.0)
    scoring_profile = Column(String(50), nullable=True)
    score_components = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('model_name', 'game_name', name='_model_game_uc'),
    )