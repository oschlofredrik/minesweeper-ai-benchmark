"""Add multi-game support to database schema

Revision ID: add_multi_game_support
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_multi_game_support'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add multi-game support tables and columns."""
    
    # Create games table
    op.create_table('games_registry',
        sa.Column('game_name', sa.String(50), primary_key=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('supported_modes', sa.JSON(), nullable=False),
        sa.Column('scoring_components', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('config', sa.JSON(), nullable=True)
    )
    
    # Create competition_sessions table
    op.create_table('competition_sessions',
        sa.Column('session_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.String(50), nullable=False),  # single_round, multi_round, tournament, marathon
        sa.Column('join_code', sa.String(10), nullable=False, unique=True),
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('max_players', sa.Integer(), default=50),
        sa.Column('min_players', sa.Integer(), default=1),
        sa.Column('creator_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), default='waiting'),  # waiting, active, completed, cancelled
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),  # Full session configuration
        sa.Index('idx_join_code', 'join_code'),
        sa.Index('idx_status', 'status'),
        sa.Index('idx_creator', 'creator_id')
    )
    
    # Create session_rounds table
    op.create_table('session_rounds',
        sa.Column('round_id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('competition_sessions.session_id'), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('game_name', sa.String(50), sa.ForeignKey('games_registry.game_name'), nullable=False),
        sa.Column('game_config', sa.JSON(), nullable=False),
        sa.Column('scoring_profile', sa.JSON(), nullable=False),
        sa.Column('time_limit', sa.Integer(), nullable=True),  # seconds
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('session_id', 'round_number')
    )
    
    # Create session_players table
    op.create_table('session_players',
        sa.Column('session_id', sa.String(36), sa.ForeignKey('competition_sessions.session_id'), nullable=False),
        sa.Column('player_id', sa.String(36), nullable=False),
        sa.Column('player_name', sa.String(100), nullable=False),
        sa.Column('ai_model', sa.String(50), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_ready', sa.Boolean(), default=False),
        sa.Column('warmup_score', sa.Float(), default=0.0),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.Column('total_score', sa.Float(), default=0.0),
        sa.PrimaryKeyConstraint('session_id', 'player_id')
    )
    
    # Create prompt_library table
    op.create_table('prompt_library',
        sa.Column('prompt_id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('game_name', sa.String(50), sa.ForeignKey('games_registry.game_name'), nullable=False),
        sa.Column('template_id', sa.String(36), nullable=True),
        sa.Column('visibility', sa.String(20), default='private'),  # private, friends, public, team
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('parent_id', sa.String(36), nullable=True),  # For versioning
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('total_score', sa.Float(), default=0.0),
        sa.Column('avg_score', sa.Float(), default=0.0),
        sa.Column('win_rate', sa.Float(), default=0.0),
        sa.Column('likes', sa.Integer(), default=0),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Index('idx_owner', 'owner_id'),
        sa.Index('idx_game', 'game_name'),
        sa.Index('idx_visibility', 'visibility'),
        sa.Index('idx_parent', 'parent_id')
    )
    
    # Create spectator_sessions table
    op.create_table('spectator_sessions',
        sa.Column('spectator_id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('competition_sessions.session_id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('view_mode', sa.String(20), default='overview'),
        sa.Column('prediction_score', sa.Integer(), default=0),
        sa.Column('watch_time', sa.Integer(), default=0),  # seconds
        sa.Column('interactions', sa.Integer(), default=0)
    )
    
    # Update existing games table to add game_name column
    with op.batch_alter_table('games') as batch_op:
        batch_op.add_column(sa.Column('game_name', sa.String(50), nullable=True, server_default='minesweeper'))
        batch_op.add_column(sa.Column('session_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('round_number', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('prompt_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('ai_model', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('evaluation_time', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_components', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('final_score', sa.Float(), nullable=True))
        batch_op.create_index('idx_game_name', ['game_name'])
        batch_op.create_index('idx_session_round', ['session_id', 'round_number'])
    
    # Update leaderboard_entries to support multiple games
    with op.batch_alter_table('leaderboard_entries') as batch_op:
        batch_op.add_column(sa.Column('game_name', sa.String(50), nullable=True, server_default='minesweeper'))
        batch_op.add_column(sa.Column('scoring_profile', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('score_components', sa.JSON(), nullable=True))
        # Update unique constraint to include game_name
        batch_op.drop_constraint('_model_name_uc', type_='unique')
        batch_op.create_unique_constraint('_model_game_uc', ['model_name', 'game_name'])
    
    # Create scoring_profiles table
    op.create_table('scoring_profiles',
        sa.Column('profile_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weights', sa.JSON(), nullable=False),  # Component weights
        sa.Column('is_preset', sa.Boolean(), default=False),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Create player_profiles table
    op.create_table('player_profiles',
        sa.Column('player_id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('total_games', sa.Integer(), default=0),
        sa.Column('total_wins', sa.Integer(), default=0),
        sa.Column('skill_ratings', sa.JSON(), nullable=True),  # Per-game ratings
        sa.Column('achievements', sa.JSON(), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True)
    )
    
    # Create queue_items table for evaluation tracking
    op.create_table('queue_items',
        sa.Column('item_id', sa.String(36), primary_key=True),
        sa.Column('player_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('game_name', sa.String(50), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), default=2),  # 1=high, 2=normal, 3=low
        sa.Column('status', sa.String(20), default='queued'),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('worker_id', sa.String(36), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Index('idx_status', 'status'),
        sa.Index('idx_session_round', 'session_id', 'round_number')
    )
    
    # Insert default scoring profiles
    op.execute("""
        INSERT INTO scoring_profiles (profile_id, name, description, weights, is_preset)
        VALUES 
        ('speed_demon', 'Speed Demon', 'Prioritizes fast completion', 
         '{"speed": 0.7, "completion": 0.2, "accuracy": 0.1}', 1),
        ('perfectionist', 'Perfectionist', 'Values accuracy and correctness',
         '{"accuracy": 0.5, "efficiency": 0.3, "reasoning": 0.2}', 1),
        ('efficiency_master', 'Efficiency Master', 'Rewards optimal solutions',
         '{"efficiency": 0.6, "accuracy": 0.3, "speed": 0.1}', 1),
        ('creative_challenge', 'Creative Challenge', 'Rewards novel approaches',
         '{"creativity": 0.4, "completion": 0.3, "reasoning": 0.3}', 1),
        ('balanced', 'Balanced', 'Equal weight to all components',
         '{"completion": 0.2, "speed": 0.2, "accuracy": 0.2, "efficiency": 0.2, "reasoning": 0.2}', 1)
    """)


def downgrade():
    """Remove multi-game support."""
    # Drop new tables
    op.drop_table('queue_items')
    op.drop_table('player_profiles')
    op.drop_table('scoring_profiles')
    op.drop_table('spectator_sessions')
    op.drop_table('prompt_library')
    op.drop_table('session_players')
    op.drop_table('session_rounds')
    op.drop_table('competition_sessions')
    op.drop_table('games_registry')
    
    # Remove columns from existing tables
    with op.batch_alter_table('games') as batch_op:
        batch_op.drop_index('idx_game_name')
        batch_op.drop_index('idx_session_round')
        batch_op.drop_column('game_name')
        batch_op.drop_column('session_id')
        batch_op.drop_column('round_number')
        batch_op.drop_column('prompt_id')
        batch_op.drop_column('ai_model')
        batch_op.drop_column('evaluation_time')
        batch_op.drop_column('score_components')
        batch_op.drop_column('final_score')
    
    with op.batch_alter_table('leaderboard_entries') as batch_op:
        batch_op.drop_constraint('_model_game_uc', type_='unique')
        batch_op.create_unique_constraint('_model_name_uc', ['model_name'])
        batch_op.drop_column('game_name')
        batch_op.drop_column('scoring_profile')
        batch_op.drop_column('score_components')