"""
Database models for the dynamic evaluation system.
"""

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, 
    DateTime, ForeignKey, Text, JSON, DECIMAL,
    CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()


class Evaluation(Base):
    """Core evaluation definition"""
    __tablename__ = 'evaluations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), default='1.0')
    scoring_type = Column(String(50), CheckConstraint(
        "scoring_type IN ('binary', 'proportional', 'cumulative')"
    ))
    rules = Column(JSON, nullable=False)
    normalization_config = Column(JSON)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = Column(Boolean, default=False)
    category = Column(String(100))
    tags = Column(ARRAY(Text))
    
    # Relationships
    templates = relationship("EvaluationTemplate", back_populates="evaluation")
    game_evaluations = relationship("GameEvaluation", back_populates="evaluation")
    scores = relationship("EvaluationScore", back_populates="evaluation")
    reviews = relationship("EvaluationReview", back_populates="evaluation")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_evaluations_category', 'category'),
        Index('idx_evaluations_is_public', 'is_public'),
        Index('idx_evaluations_created_by', 'created_by'),
    )


class EvaluationTemplate(Base):
    """Marketplace templates for evaluations"""
    __tablename__ = 'evaluation_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.id'))
    downloads = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2))
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="templates")
    
    # Indexes
    __table_args__ = (
        Index('idx_templates_rating', 'rating'),
        Index('idx_templates_downloads', 'downloads'),
        Index('idx_templates_featured', 'featured'),
    )


class GameEvaluation(Base):
    """Links evaluations to game sessions"""
    __tablename__ = 'game_evaluations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_session_id = Column(UUID(as_uuid=True), nullable=False)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.id'))
    weight = Column(DECIMAL(3, 2), CheckConstraint('weight >= 0 AND weight <= 1'))
    dimension = Column(String(100))
    config_overrides = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="game_evaluations")
    
    # Indexes
    __table_args__ = (
        Index('idx_game_evaluations_session', 'game_session_id'),
        UniqueConstraint('game_session_id', 'evaluation_id', name='uq_game_evaluation'),
    )


class EvaluationScore(Base):
    """Stores evaluation results"""
    __tablename__ = 'evaluation_scores'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_session_id = Column(UUID(as_uuid=True), nullable=False)
    player_id = Column(UUID(as_uuid=True), nullable=False)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.id'))
    round_number = Column(Integer)
    raw_score = Column(Float)
    normalized_score = Column(Float)
    rule_breakdown = Column(JSON)
    dimension_scores = Column(JSON)
    context_snapshot = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="scores")
    
    # Indexes
    __table_args__ = (
        Index('idx_scores_session', 'game_session_id'),
        Index('idx_scores_player', 'player_id'),
        Index('idx_scores_round', 'round_number'),
        Index('idx_scores_created', 'created_at'),
    )


class EvaluationReview(Base):
    """User reviews and ratings for evaluations"""
    __tablename__ = 'evaluation_reviews'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.id'))
    user_id = Column(UUID(as_uuid=True), nullable=False)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    review = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="reviews")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('evaluation_id', 'user_id', name='uq_user_review'),
        Index('idx_reviews_evaluation', 'evaluation_id'),
        Index('idx_reviews_rating', 'rating'),
    )


# Additional models for advanced features

class EvaluationVersion(Base):
    """Version history for evaluations"""
    __tablename__ = 'evaluation_versions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.id'))
    version = Column(String(50), nullable=False)
    rules = Column(JSON, nullable=False)
    normalization_config = Column(JSON)
    change_summary = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_versions_evaluation', 'evaluation_id'),
        UniqueConstraint('evaluation_id', 'version', name='uq_evaluation_version'),
    )


class EvaluationDimension(Base):
    """Predefined evaluation dimensions"""
    __tablename__ = 'evaluation_dimensions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    color = Column(String(7))  # Hex color
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationPreset(Base):
    """Preset evaluation configurations for quick setup"""
    __tablename__ = 'evaluation_presets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    evaluation_ids = Column(ARRAY(UUID(as_uuid=True)))
    weights = Column(JSON)  # {"eval_id": weight}
    tags = Column(ARRAY(Text))
    difficulty = Column(String(20))  # easy, medium, hard, expert
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_presets_difficulty', 'difficulty'),
        Index('idx_presets_featured', 'is_featured'),
    )