"""Game registry system for managing available games."""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from .base import BaseGame, GameConfig, GameInstance, GameMode


logger = logging.getLogger(__name__)


class GameRegistry:
    """Registry for managing available games in the platform."""
    
    def __init__(self):
        self._games: Dict[str, Type[BaseGame]] = {}
        self._instances: Dict[str, BaseGame] = {}
    
    def register_game(self, game_class: Type[BaseGame]) -> None:
        """Register a new game class."""
        if not issubclass(game_class, BaseGame):
            raise ValueError(f"{game_class} must inherit from BaseGame")
        
        # Create instance to get name
        game_instance = game_class()
        game_name = game_instance.name
        
        if game_name in self._games:
            logger.warning(f"Game '{game_name}' is already registered. Overwriting.")
        
        self._games[game_name] = game_class
        self._instances[game_name] = game_instance
        logger.info(f"Registered game: {game_name} ({game_instance.display_name})")
    
    def unregister_game(self, game_name: str) -> None:
        """Unregister a game."""
        if game_name in self._games:
            del self._games[game_name]
            del self._instances[game_name]
            logger.info(f"Unregistered game: {game_name}")
    
    def get_game(self, game_name: str) -> Optional[BaseGame]:
        """Get a game instance by name."""
        return self._instances.get(game_name)
    
    def get_game_class(self, game_name: str) -> Optional[Type[BaseGame]]:
        """Get a game class by name."""
        return self._games.get(game_name)
    
    def list_games(self) -> List[Dict[str, str]]:
        """List all registered games."""
        games = []
        for name, instance in self._instances.items():
            games.append({
                "name": name,
                "display_name": instance.display_name,
                "description": instance.description,
                "supported_modes": [mode.value for mode in instance.supported_modes]
            })
        return games
    
    def get_games_by_mode(self, mode: GameMode) -> List[str]:
        """Get games that support a specific mode."""
        games = []
        for name, instance in self._instances.items():
            if mode in instance.supported_modes:
                games.append(name)
        return games
    
    def create_game_instance(self, game_name: str, config: GameConfig) -> Optional[GameInstance]:
        """Create a new instance of a game."""
        game = self.get_game(game_name)
        if not game:
            logger.error(f"Game '{game_name}' not found in registry")
            return None
        
        try:
            return game.create_instance(config)
        except Exception as e:
            logger.error(f"Failed to create instance of '{game_name}': {e}")
            return None
    
    def auto_discover_games(self, games_dir: Path) -> None:
        """
        Automatically discover and register games from a directory.
        
        Looks for Python files in the games directory and registers any
        classes that inherit from BaseGame.
        """
        if not games_dir.exists():
            logger.warning(f"Games directory does not exist: {games_dir}")
            return
        
        # Look for Python files
        for py_file in games_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            # Convert file path to module path
            # For src/games/implementations/minesweeper.py -> src.games.implementations.minesweeper
            relative_path = py_file.relative_to(Path(__file__).parent.parent.parent)
            module_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]
            
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Look for BaseGame subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseGame) and 
                        obj != BaseGame and
                        not inspect.isabstract(obj)):
                        
                        self.register_game(obj)
                        logger.info(f"Auto-discovered game: {name} from {module_path}")
                        
            except Exception as e:
                logger.error(f"Failed to import {module_path}: {e}")


# Global registry instance
game_registry = GameRegistry()


class GameLoader:
    """Utility class for loading games with various configurations."""
    
    def __init__(self, registry: GameRegistry = None):
        self.registry = registry or game_registry
    
    def load_featured_games(self) -> List[BaseGame]:
        """Load games marked as featured for the home page."""
        # In a real implementation, this might read from a config file
        featured_names = ["minesweeper", "sudoku", "chess_puzzles", "tower_of_hanoi"]
        
        games = []
        for name in featured_names:
            game = self.registry.get_game(name)
            if game:
                games.append(game)
        
        return games
    
    def load_games_for_competition(self, competition_config: Dict) -> List[BaseGame]:
        """Load games based on competition configuration."""
        games = []
        
        # Example config format:
        # {
        #     "games": ["minesweeper", "sudoku"],
        #     "mode": "speed",
        #     "difficulty_progression": ["easy", "medium", "hard"]
        # }
        
        game_names = competition_config.get("games", [])
        mode = GameMode(competition_config.get("mode", "mixed"))
        
        for name in game_names:
            game = self.registry.get_game(name)
            if game and mode in game.supported_modes:
                games.append(game)
            elif game:
                logger.warning(f"Game '{name}' does not support mode '{mode.value}'")
        
        return games
    
    def get_game_metadata(self, game_name: str) -> Optional[Dict]:
        """Get detailed metadata about a game."""
        game = self.registry.get_game(game_name)
        if not game:
            return None
        
        return {
            "name": game.name,
            "display_name": game.display_name,
            "description": game.description,
            "supported_modes": [mode.value for mode in game.supported_modes],
            "scoring_components": [
                {
                    "name": comp.name,
                    "description": comp.description,
                    "min_value": comp.min_value,
                    "max_value": comp.max_value,
                    "higher_is_better": comp.higher_is_better
                }
                for comp in game.get_scoring_components()
            ],
            "ai_prompt_template": game.get_ai_prompt_template(),
            "move_format": game.get_move_format_description()
        }


def register_builtin_games():
    """Register all built-in games."""
    # This will be called on startup to register default games
    from pathlib import Path
    games_dir = Path(__file__).parent / "implementations"
    
    if games_dir.exists():
        game_registry.auto_discover_games(games_dir)