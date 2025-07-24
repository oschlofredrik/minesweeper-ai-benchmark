"""Minesweeper game plugin implementation."""

import random
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import uuid

from src.games.base import (
    BaseGame, GameInstance, GameState, GameAction, GameResult,
    GameConfig, GameMode, ScoringComponent, AIGameInterface
)
from src.games.tilts.board import TiltsBoard
from src.games.tilts.solver import TiltsSolver


class MinesweeperGame(BaseGame):
    """Minesweeper game implementation as a plugin."""
    
    @property
    def name(self) -> str:
        return "minesweeper"
    
    @property
    def display_name(self) -> str:
        return "Minesweeper"
    
    @property
    def description(self) -> str:
        return "Classic logic puzzle where players uncover cells while avoiding hidden mines"
    
    @property
    def supported_modes(self) -> List[GameMode]:
        return [
            GameMode.SPEED,
            GameMode.ACCURACY,
            GameMode.EFFICIENCY,
            GameMode.REASONING,
            GameMode.MIXED
        ]
    
    def get_scoring_components(self) -> List[ScoringComponent]:
        return [
            ScoringComponent(
                name="completion",
                description="Whether the game was won",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="speed",
                description="Time taken to complete",
                min_value=0.0,
                max_value=float('inf'),
                higher_is_better=False
            ),
            ScoringComponent(
                name="accuracy",
                description="Percentage of safe cells correctly identified",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="efficiency",
                description="Ratio of optimal moves to actual moves",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="mine_detection",
                description="Precision of mine identification through flags",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="board_coverage",
                description="Percentage of safe cells revealed",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            )
        ]
    
    def create_instance(self, config: GameConfig) -> GameInstance:
        """Create a new Minesweeper game instance."""
        return MinesweeperInstance(config, str(uuid.uuid4()))
    
    def get_ai_prompt_template(self) -> str:
        return """You are playing Minesweeper. The board shows:
- Hidden cells: '?'
- Revealed cells: numbers 0-8 (indicating adjacent mines)
- Flagged cells: 'F'

Your goal is to reveal all safe cells without hitting mines.

Board state:
{board_state}

Game info:
- Board size: {rows}x{cols}
- Total mines: {total_mines}
- Cells revealed: {cells_revealed}
- Flags placed: {flags_placed}

Make your move using the provided function."""
    
    def get_move_format_description(self) -> str:
        return """Moves are specified as:
- action_type: "reveal", "flag", or "unflag"
- parameters: {"row": <0-based row>, "col": <0-based column>}
- reasoning: Your explanation for this move"""
    
    def get_visualization_data(self, state: GameState) -> Dict[str, Any]:
        """Get data for frontend visualization."""
        return {
            "type": "grid",
            "board": state.state_data.get("board_ascii", ""),
            "rows": state.state_data.get("rows", 0),
            "cols": state.state_data.get("cols", 0),
            "cells": state.state_data.get("cells", []),
            "game_status": state.state_data.get("status", "in_progress")
        }


class MinesweeperInstance(GameInstance):
    """A single instance of a Minesweeper game."""
    
    def __init__(self, config: GameConfig, instance_id: str):
        super().__init__(config, instance_id)
        
        # Get board configuration from difficulty
        rows, cols, mines = self._get_board_config(config.difficulty)
        
        # Allow custom overrides
        if "rows" in config.custom_settings:
            rows = config.custom_settings["rows"]
        if "cols" in config.custom_settings:
            cols = config.custom_settings["cols"]
        if "mines" in config.custom_settings:
            mines = config.custom_settings["mines"]
        
        # Create the board
        seed = config.custom_settings.get("seed", None)
        self.board = TiltsBoard(rows, cols, mines, seed)
        self.solver = TiltsSolver(self.board)
        
        # Game state
        self.game_over = False
        self.victory = False
        self.cells_revealed = 0
        self.flags_placed = 0
        self.first_move = True
    
    def _get_board_config(self, difficulty: str) -> Tuple[int, int, int]:
        """Get board configuration based on difficulty."""
        configs = {
            "easy": (9, 9, 10),
            "medium": (16, 16, 40),
            "hard": (16, 30, 99),
            "expert": (20, 40, 160)
        }
        return configs.get(difficulty, (16, 16, 40))
    
    def get_initial_state(self) -> GameState:
        """Get the initial game state."""
        return self._create_game_state()
    
    def _create_game_state(self) -> GameState:
        """Create current game state."""
        # Get possible actions
        possible_actions = []
        
        if not self.game_over:
            for row in range(self.board.rows):
                for col in range(self.board.cols):
                    cell = self.board.get_cell({"row": row, "col": col})
                    
                    if cell.is_hidden and not cell.is_flagged:
                        possible_actions.append(GameAction(
                            action_type="reveal",
                            parameters={"row": row, "col": col}
                        ))
                        possible_actions.append(GameAction(
                            action_type="flag",
                            parameters={"row": row, "col": col}
                        ))
                    elif cell.is_flagged:
                        possible_actions.append(GameAction(
                            action_type="unflag",
                            parameters={"row": row, "col": col}
                        ))
        
        # Get board visualization
        cells = []
        for row in range(self.board.rows):
            row_cells = []
            for col in range(self.board.cols):
                cell = self.board.get_cell({"row": row, "col": col})
                cell_data = {
                    "row": row,
                    "col": col,
                    "is_revealed": cell.is_revealed,
                    "is_flagged": cell.is_flagged,
                    "adjacent_mines": cell.adjacent_mines if cell.is_revealed else None,
                    "has_mine": cell.has_mine if self.game_over else None
                }
                row_cells.append(cell_data)
            cells.append(row_cells)
        
        return GameState(
            state_data={
                "board_ascii": self.board.to_ascii(show_mines=self.game_over),
                "rows": self.board.rows,
                "cols": self.board.cols,
                "total_mines": self.board.total_mines,
                "cells_revealed": self.cells_revealed,
                "flags_placed": self.flags_placed,
                "cells": cells,
                "status": "won" if self.victory else "lost" if self.game_over else "in_progress"
            },
            is_terminal=self.game_over,
            is_victory=self.victory,
            possible_actions=possible_actions
        )
    
    def apply_action(self, state: GameState, action: GameAction) -> Tuple[GameState, bool, str]:
        """Apply an action to the game state."""
        if self.game_over:
            return state, False, "Game is already over"
        
        row = action.parameters.get("row")
        col = action.parameters.get("col")
        
        if row is None or col is None:
            return state, False, "Missing row or col in parameters"
        
        if not (0 <= row < self.board.rows and 0 <= col < self.board.cols):
            return state, False, f"Invalid position ({row}, {col})"
        
        pos = {"row": row, "col": col}
        cell = self.board.get_cell(pos)
        
        if action.action_type == "reveal":
            if cell.is_revealed:
                return state, False, "Cell is already revealed"
            if cell.is_flagged:
                return state, False, "Cannot reveal flagged cell"
            
            # Handle first move safety
            if self.first_move and cell.has_mine:
                self._relocate_mine(pos)
            self.first_move = False
            
            # Reveal the cell
            hit_mine, revealed_positions = self.board.reveal_cell(pos)
            
            if hit_mine:
                self.game_over = True
                self.victory = False
            else:
                self.cells_revealed += len(revealed_positions)
                # Check for victory
                non_mine_cells = self.board.rows * self.board.cols - self.board.total_mines
                if self.cells_revealed == non_mine_cells:
                    self.game_over = True
                    self.victory = True
            
        elif action.action_type == "flag":
            if not self.board.flag_cell(pos):
                return state, False, "Cannot flag this cell"
            self.flags_placed += 1
            
        elif action.action_type == "unflag":
            if not self.board.unflag_cell(pos):
                return state, False, "Cell is not flagged"
            self.flags_placed -= 1
        
        else:
            return state, False, f"Unknown action type: {action.action_type}"
        
        # Return new state
        new_state = self._create_game_state()
        return new_state, True, ""
    
    def _relocate_mine(self, pos: Dict[str, int]):
        """Relocate mine for first move safety."""
        # Find a safe position without a mine
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                new_pos = {"row": row, "col": col}
                if new_pos != pos and not self.board.get_cell(new_pos).has_mine:
                    # Move mine
                    self.board.get_cell(pos).has_mine = False
                    self.board.get_cell(new_pos).has_mine = True
                    # Recalculate adjacent mines
                    self.board._calculate_adjacent_mines()
                    return
    
    def calculate_score_components(self, result: GameResult) -> Dict[str, float]:
        """Calculate scoring components for the game."""
        components = {}
        
        # Completion
        components["completion"] = 1.0 if result.victory else 0.0
        
        # Speed (raw seconds, will be normalized by scoring system)
        components["speed"] = result.time_taken
        
        # Accuracy - percentage of safe cells correctly identified
        total_cells = self.board.rows * self.board.cols
        safe_cells = total_cells - self.board.total_mines
        components["accuracy"] = self.cells_revealed / safe_cells if safe_cells > 0 else 0
        
        # Efficiency - compare to optimal solver
        if result.moves_made > 0:
            optimal_moves = self.get_optimal_moves(result.final_state)
            components["efficiency"] = min(1.0, optimal_moves / result.moves_made)
        else:
            components["efficiency"] = 0.0
        
        # Mine detection - precision of flags
        if self.flags_placed > 0:
            correct_flags = sum(
                1 for row in range(self.board.rows)
                for col in range(self.board.cols)
                if self.board.get_cell({"row": row, "col": col}).is_flagged
                and self.board.get_cell({"row": row, "col": col}).has_mine
            )
            components["mine_detection"] = correct_flags / self.flags_placed
        else:
            components["mine_detection"] = 0.0
        
        # Board coverage
        components["board_coverage"] = components["accuracy"]  # Same as accuracy
        
        return components
    
    def get_optimal_moves(self, state: GameState) -> int:
        """Estimate optimal moves for the current state."""
        # Use solver to estimate
        safe_moves = self.solver.get_safe_moves()
        if safe_moves:
            return len(safe_moves)
        
        # Fallback: estimate based on remaining cells
        remaining = (self.board.rows * self.board.cols - 
                    self.board.total_mines - self.cells_revealed)
        return max(1, remaining // 3)  # Rough estimate


class MinesweeperAIInterface(AIGameInterface):
    """AI interface for Minesweeper."""
    
    def get_function_calling_schema(self) -> Dict[str, Any]:
        """Get OpenAI/Anthropic function calling schema."""
        return {
            "name": "make_move",
            "description": "Make a move in Minesweeper",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reveal", "flag", "unflag"],
                        "description": "The action to perform"
                    },
                    "row": {
                        "type": "integer",
                        "description": "The row index (0-based)"
                    },
                    "col": {
                        "type": "integer",
                        "description": "The column index (0-based)"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for this move"
                    }
                },
                "required": ["action", "row", "col", "reasoning"]
            }
        }
    
    def parse_ai_response(self, response: Dict[str, Any]) -> GameAction:
        """Parse AI function call response."""
        return GameAction(
            action_type=response.get("action", ""),
            parameters={
                "row": response.get("row", 0),
                "col": response.get("col", 0)
            },
            reasoning=response.get("reasoning", "")
        )
    
    def format_state_for_ai(self, state: GameState, config: GameConfig) -> str:
        """Format game state for AI based on mode."""
        template = MinesweeperGame().get_ai_prompt_template()
        
        # Add mode-specific instructions
        mode_instructions = {
            GameMode.SPEED: "\nPlay quickly but safely. Time is critical!",
            GameMode.ACCURACY: "\nFocus on accuracy. Avoid any risky moves.",
            GameMode.EFFICIENCY: "\nUse the minimum number of moves. Think strategically.",
            GameMode.REASONING: "\nProvide detailed reasoning for each move.",
            GameMode.CREATIVE: "\nBe creative in your approach and explain your strategy."
        }
        
        instruction = mode_instructions.get(config.mode, "")
        
        return template.format(
            board_state=state.state_data["board_ascii"],
            rows=state.state_data["rows"],
            cols=state.state_data["cols"],
            total_mines=state.state_data["total_mines"],
            cells_revealed=state.state_data["cells_revealed"],
            flags_placed=state.state_data["flags_placed"]
        ) + instruction