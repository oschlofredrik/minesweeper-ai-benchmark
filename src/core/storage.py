"""Storage layer that supports both database and file-based storage."""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import (
    get_db, init_db, Game, Evaluation, Task, PromptTemplate, 
    LeaderboardEntry, game_to_dict, evaluation_to_dict
)
from src.core.types import GameTranscript, EvaluationMetrics, ModelConfig

logger = logging.getLogger(__name__)


class StorageBackend:
    """Unified storage backend supporting both database and file storage."""
    
    def __init__(self):
        self.use_database = os.getenv('DATABASE_URL') is not None
        if self.use_database:
            try:
                init_db()
                logger.info("Using database storage backend")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                logger.info("Falling back to file storage")
                self.use_database = False
        else:
            logger.info("Using file storage backend")
    
    # Game Storage Methods
    def save_game(self, game_result: GameTranscript) -> str:
        """Save a game result."""
        if self.use_database:
            return self._save_game_to_db(game_result)
        else:
            return self._save_game_to_file(game_result)
    
    def load_game(self, game_id: str) -> Optional[GameTranscript]:
        """Load a game by ID."""
        if self.use_database:
            return self._load_game_from_db(game_id)
        else:
            return self._load_game_from_file(game_id)
    
    def list_games(self, model_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List games, optionally filtered by model."""
        if self.use_database:
            return self._list_games_from_db(model_name, limit)
        else:
            return self._list_games_from_files(model_name, limit)
    
    # Evaluation Storage Methods
    def save_evaluation(self, game_id: str, metrics: EvaluationMetrics, 
                       reasoning_analysis: Optional[Dict] = None,
                       total_time: Optional[float] = None) -> bool:
        """Save evaluation metrics for a game."""
        if self.use_database:
            return self._save_evaluation_to_db(game_id, metrics, reasoning_analysis, total_time)
        else:
            return self._save_evaluation_to_file(game_id, metrics, reasoning_analysis, total_time)
    
    # Task Storage Methods  
    def save_task(self, task_data: Dict[str, Any]) -> str:
        """Save a benchmark task."""
        if self.use_database:
            return self._save_task_to_db(task_data)
        else:
            return self._save_task_to_file(task_data)
    
    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load a task by ID."""
        if self.use_database:
            return self._load_task_from_db(task_id)
        else:
            return self._load_task_from_file(task_id)
    
    def list_tasks(self, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tasks."""
        if self.use_database:
            return self._list_tasks_from_db(difficulty)
        else:
            return self._list_tasks_from_files(difficulty)
    
    # Leaderboard Methods
    def update_leaderboard(self, model_config: ModelConfig, metrics: Dict[str, float]) -> bool:
        """Update leaderboard entry for a model."""
        if self.use_database:
            return self._update_leaderboard_db(model_config, metrics)
        else:
            # File-based leaderboard is computed on-demand
            return True
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get leaderboard entries."""
        if self.use_database:
            return self._get_leaderboard_from_db()
        else:
            return self._compute_leaderboard_from_files()
    
    # Database Implementation Methods
    def _save_game_to_db(self, game_result: GameTranscript) -> str:
        """Save game to database."""
        try:
            db = next(get_db())
            
            game = Game(
                id=game_result.game_id,
                model_provider=game_result.model_config.provider,
                model_name=game_result.model_config.name,
                difficulty=game_result.difficulty,
                rows=game_result.board_size[0],
                cols=game_result.board_size[1],
                mines=game_result.mine_count,
                initial_board=game_result.initial_board,
                final_board=game_result.final_board,
                moves=[move.to_dict() for move in game_result.moves],
                won=game_result.won,
                num_moves=game_result.num_moves,
                valid_moves=game_result.valid_moves,
                invalid_moves=game_result.invalid_moves,
                flags_placed=game_result.flags_placed,
                cells_revealed=game_result.cells_revealed,
                completed_at=datetime.utcnow()
            )
            
            db.add(game)
            db.commit()
            
            return game_result.game_id
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving game: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _load_game_from_db(self, game_id: str) -> Optional[GameTranscript]:
        """Load game from database."""
        try:
            db = next(get_db())
            game = db.query(Game).filter(Game.id == game_id).first()
            
            if not game:
                return None
            
            # Convert back to GameTranscript
            # This is simplified - you'd need proper conversion logic
            game_dict = game_to_dict(game)
            return GameTranscript.from_dict(game_dict)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading game: {e}")
            return None
        finally:
            db.close()
    
    def _list_games_from_db(self, model_name: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """List games from database."""
        try:
            db = next(get_db())
            query = db.query(Game)
            
            if model_name:
                query = query.filter(Game.model_name == model_name)
            
            games = query.order_by(Game.created_at.desc()).limit(limit).all()
            
            return [game_to_dict(game) for game in games]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing games: {e}")
            return []
        finally:
            db.close()
    
    def _save_evaluation_to_db(self, game_id: str, metrics: EvaluationMetrics,
                               reasoning_analysis: Optional[Dict],
                               total_time: Optional[float]) -> bool:
        """Save evaluation to database."""
        try:
            db = next(get_db())
            
            evaluation = Evaluation(
                game_id=game_id,
                win_rate=metrics.win_rate,
                valid_move_rate=metrics.valid_move_rate,
                mine_identification_precision=metrics.mine_identification_precision,
                mine_identification_recall=metrics.mine_identification_recall,
                board_coverage=metrics.board_coverage,
                efficiency_score=metrics.efficiency_score,
                strategic_score=metrics.strategic_score,
                reasoning_score=metrics.reasoning_score,
                composite_score=metrics.composite_score,
                total_time_seconds=total_time,
                reasoning_analysis=reasoning_analysis
            )
            
            db.add(evaluation)
            db.commit()
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving evaluation: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    # File Storage Implementation Methods (existing functionality)
    def _save_game_to_file(self, game_result: GameTranscript) -> str:
        """Save game to file (existing implementation)."""
        data_dir = Path("data/games")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = data_dir / f"{game_result.game_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(game_result.to_dict(), f, indent=2)
        
        return game_result.game_id
    
    def _load_game_from_file(self, game_id: str) -> Optional[GameTranscript]:
        """Load game from file."""
        file_path = Path(f"data/games/{game_id}.json")
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return GameResult.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading game file: {e}")
            return None
    
    def _list_games_from_files(self, model_name: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """List games from files."""
        games_dir = Path("data/games")
        if not games_dir.exists():
            return []
        
        games = []
        for file_path in sorted(games_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                
                if model_name and game_data.get('model', {}).get('name') != model_name:
                    continue
                
                games.append(game_data)
            except Exception as e:
                logger.error(f"Error reading game file {file_path}: {e}")
        
        return games
    
    def _save_task_to_file(self, task_data: Dict[str, Any]) -> str:
        """Save task to file."""
        data_dir = Path("data/tasks")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        task_id = task_data['task_id']
        file_path = data_dir / f"{task_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        return task_id
    
    def _load_task_from_file(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task from file."""
        file_path = Path(f"data/tasks/{task_id}.json")
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading task file: {e}")
            return None
    
    def _save_task_to_db(self, task_data: Dict[str, Any]) -> str:
        """Save task to database."""
        try:
            db = next(get_db())
            
            task = Task(
                id=task_data['task_id'],
                difficulty=task_data['difficulty'],
                rows=task_data['board_size'][0],
                cols=task_data['board_size'][1],
                mines=task_data['mine_count'],
                mine_positions=task_data['mine_positions'],
                initial_state=task_data.get('initial_state', {})
            )
            
            db.add(task)
            db.commit()
            
            return task_data['task_id']
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving task: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _list_tasks_from_files(self, difficulty: Optional[str]) -> List[Dict[str, Any]]:
        """List tasks from files."""
        tasks_dir = Path("data/tasks")
        if not tasks_dir.exists():
            return []
        
        tasks = []
        for file_path in tasks_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    task_data = json.load(f)
                
                if difficulty and task_data.get('difficulty') != difficulty:
                    continue
                
                tasks.append(task_data)
            except Exception as e:
                logger.error(f"Error reading task file {file_path}: {e}")
        
        return tasks
    
    def _compute_leaderboard_from_files(self) -> List[Dict[str, Any]]:
        """Compute leaderboard from files (existing logic)."""
        # This would aggregate metrics from result files
        # For now, return empty list
        return []
    
    def _save_evaluation_to_file(self, game_id: str, metrics: EvaluationMetrics,
                                reasoning_analysis: Optional[Dict],
                                total_time: Optional[float]) -> bool:
        """Save evaluation to file."""
        # For file-based storage, evaluations are part of the game result
        # This is a no-op for backward compatibility
        return True


# Global storage instance
_storage = None

def get_storage() -> StorageBackend:
    """Get the storage backend instance."""
    global _storage
    if _storage is None:
        _storage = StorageBackend()
    return _storage