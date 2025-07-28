"""Adapter to make any game compatible with the TiltsGame interface."""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
from enum import Enum

from src.core.types import GameTranscript, GameState, Action, ActionType, Position, GameStatus
from src.games.base_game import GameInstance, GameAction


class GameAdapter:
    """Adapts any game to work with the Minesweeper-focused evaluation system."""
    
    def __init__(self, game_instance: GameInstance, task_id: str, model_name: str):
        self.game_instance = game_instance
        self.task_id = task_id
        self.model_name = model_name
        self.start_time = datetime.now(timezone.utc)
        self.end_time = None
        self.moves = []
        self.status = GameStatus.IN_PROGRESS
        self.error_message = None
        
        # For compatibility with board-based code
        self.board = self._create_board_proxy()
    
    def _create_board_proxy(self):
        """Create a proxy object for board compatibility."""
        class BoardProxy:
            def __init__(self, game_instance):
                self.game = game_instance
                # Default sizes for non-board games
                self.rows = 10
                self.cols = 10
                self.total_mines = 0
            
            def to_coordinate_list(self):
                """Return empty coordinate list for non-board games."""
                return {
                    "board_size": {"rows": self.rows, "cols": self.cols},
                    "revealed": [],
                    "flagged": []
                }
        
        return BoardProxy(self.game_instance)
    
    def get_board_representation(self, format: str = "ascii") -> str:
        """Get board representation for AI."""
        # For non-Minesweeper games, use the game's AI representation
        state = self.game_instance.get_state()
        
        # Check if the state has an AI representation method
        if hasattr(state, 'ai_representation') and hasattr(state.ai_representation, 'get_prompt'):
            return state.ai_representation.get_prompt()
        elif hasattr(state, 'get_ai_representation'):
            return state.get_ai_representation()
        else:
            # Fallback to string representation
            return str(state)
    
    def make_move(self, action: Action, ai_details: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Make a move in the game."""
        try:
            # Convert Minesweeper-style action to game-specific action
            game_action = self._convert_action(action)
            
            # Execute move
            success = self.game_instance.make_move(self.game_instance.current_player(), game_action)
            
            if success:
                message = "Move executed successfully"
                game_status = self._get_game_status()
                
                # Record move
                move_data = {
                    "action": action,
                    "was_valid": True,
                    "timestamp": datetime.now(timezone.utc),
                    "model_reasoning": ai_details.get("model_reasoning") if ai_details else None,
                    "prompt_sent": ai_details.get("prompt_sent") if ai_details else None,
                    "full_response": ai_details.get("full_response") if ai_details else None,
                    "tokens_used": ai_details.get("tokens_used") if ai_details else None,
                }
                self.moves.append(move_data)
                
                # Update status
                if game_status == "won":
                    self.status = GameStatus.WON
                    self.end_time = datetime.now(timezone.utc)
                elif game_status == "lost":
                    self.status = GameStatus.LOST
                    self.end_time = datetime.now(timezone.utc)
                
                return True, message, {"game_status": game_status}
            else:
                return False, "Invalid move", {}
                
        except Exception as e:
            return False, str(e), {}
    
    def _convert_action(self, action: Action) -> GameAction:
        """Convert Minesweeper action to game-specific action."""
        # For Risk and other games, we need to parse the actual game action
        # The action might come from function calling with proper data
        
        # If the action has function call data (from AI models using function calling)
        if hasattr(action, 'function_data') and action.function_data:
            # Extract the game-specific action from function call
            data = action.function_data
            
            # For Risk, create appropriate GameAction based on the function call
            if 'action_type' in data:
                if data['action_type'] == 'reinforce':
                    return GameAction("reinforce", {
                        "territory": data.get('territory'),
                        "armies": data.get('armies', 1)
                    })
                elif data['action_type'] == 'attack':
                    return GameAction("attack", {
                        "from_territory": data.get('from_territory'),
                        "to_territory": data.get('to_territory'),
                        "armies": data.get('armies', 3)
                    })
                elif data['action_type'] == 'fortify':
                    return GameAction("fortify", {
                        "from_territory": data.get('from_territory'),
                        "to_territory": data.get('to_territory'),
                        "armies": data.get('armies', 1)
                    })
                elif data['action_type'] == 'end_turn':
                    return GameAction("end_turn", {})
        
        # Fallback: try to create a generic action
        # This won't work well for complex games but allows basic testing
        return GameAction(action.action_type.value, {
            "position": {"row": action.position.row, "col": action.position.col}
        })
    
    def _get_game_status(self) -> str:
        """Get current game status."""
        if self.game_instance.is_finished():
            winners = self.game_instance.get_winners()
            if self.game_instance.current_player() in winners:
                return "won"
            else:
                return "lost"
        return "in_progress"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get game statistics."""
        return {
            "status": self.status.value,
            "moves_made": len(self.moves),
            "board_coverage": 0.0,  # Not applicable for non-board games
            "game_specific_stats": self.game_instance.get_state().to_dict() if hasattr(self.game_instance.get_state(), 'to_dict') else {}
        }
    
    def get_transcript(self) -> GameTranscript:
        """Get full game transcript."""
        # Build transcript compatible with evaluation system
        final_state = GameState(
            board=None,  # Not used for non-Minesweeper games
            revealed_cells={},
            flagged_cells=set(),
            status=self.status,
            moves_made=len(self.moves),
            board_coverage=0.0,
            mines_correctly_flagged=0,
            mines_incorrectly_flagged=0
        )
        
        # Convert moves to expected format
        transcript_moves = []
        for i, move_data in enumerate(self.moves):
            transcript_moves.append({
                "move_number": i + 1,
                "action": move_data["action"],
                "was_valid": move_data["was_valid"],
                "timestamp": move_data["timestamp"],
                "model_reasoning": move_data.get("model_reasoning"),
                "prompt_sent": move_data.get("prompt_sent"),
                "full_response": move_data.get("full_response"),
                "tokens_used": move_data.get("tokens_used"),
            })
        
        return GameTranscript(
            game_id=f"{self.task_id}_{self.model_name}_{self.start_time.timestamp()}",
            task_id=self.task_id,
            model_name=self.model_name,
            start_time=self.start_time,
            end_time=self.end_time or datetime.now(timezone.utc),
            moves=transcript_moves,
            final_state=final_state,
            error_message=self.error_message
        )
    
    def mark_as_error(self, error_message: str):
        """Mark game as having an error."""
        self.status = GameStatus.ERROR
        self.error_message = error_message
        self.end_time = datetime.now(timezone.utc)