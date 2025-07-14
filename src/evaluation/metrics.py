"""Metrics calculation for model evaluation."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from src.core.types import (
    GameTranscript, GameStatus, ActionType, EvaluationMetrics
)


class MetricsCalculator:
    """Calculate evaluation metrics from game transcripts."""
    
    def calculate_metrics(self, transcripts: List[GameTranscript]) -> EvaluationMetrics:
        """
        Calculate aggregate metrics from multiple game transcripts.
        
        Args:
            transcripts: List of game transcripts
        
        Returns:
            Evaluation metrics
        """
        if not transcripts:
            return self._empty_metrics()
        
        # Calculate individual metrics
        win_rate = self._calculate_win_rate(transcripts)
        valid_move_rate = self._calculate_valid_move_rate(transcripts)
        mine_precision, mine_recall = self._calculate_mine_identification_metrics(transcripts)
        avg_moves_win = self._calculate_average_moves_to_win(transcripts)
        avg_moves_loss = self._calculate_average_moves_to_loss(transcripts)
        board_coverage = self._calculate_board_coverage_on_loss(transcripts)
        reasoning_score = self._calculate_reasoning_quality(transcripts)
        
        return EvaluationMetrics(
            win_rate=win_rate,
            valid_move_rate=valid_move_rate,
            mine_identification_precision=mine_precision,
            mine_identification_recall=mine_recall,
            average_moves_to_win=avg_moves_win,
            average_moves_to_loss=avg_moves_loss,
            board_coverage_on_loss=board_coverage,
            reasoning_quality_score=reasoning_score,
        )
    
    def _empty_metrics(self) -> EvaluationMetrics:
        """Return empty metrics when no transcripts available."""
        return EvaluationMetrics(
            win_rate=0.0,
            valid_move_rate=0.0,
            mine_identification_precision=0.0,
            mine_identification_recall=0.0,
            average_moves_to_win=None,
            average_moves_to_loss=None,
            board_coverage_on_loss=0.0,
            reasoning_quality_score=None,
        )
    
    def _calculate_win_rate(self, transcripts: List[GameTranscript]) -> float:
        """Calculate percentage of games won (excluding technical failures)."""
        if not transcripts:
            return 0.0
        
        # Exclude games that failed due to technical errors
        valid_games = [t for t in transcripts if t.final_state.status != GameStatus.ERROR]
        if not valid_games:
            return 0.0
            
        wins = sum(1 for t in valid_games if t.final_state.status == GameStatus.WON)
        return wins / len(valid_games)
    
    def _calculate_valid_move_rate(self, transcripts: List[GameTranscript]) -> float:
        """Calculate percentage of valid moves across all games."""
        total_moves = 0
        valid_moves = 0
        
        for transcript in transcripts:
            for move in transcript.moves:
                total_moves += 1
                if move.was_valid:
                    valid_moves += 1
        
        return valid_moves / total_moves if total_moves > 0 else 0.0
    
    def _calculate_mine_identification_metrics(
        self, transcripts: List[GameTranscript]
    ) -> tuple[float, float]:
        """Calculate precision and recall for mine flagging."""
        total_flags = 0
        correct_flags = 0
        total_mines = 0
        flagged_mines = 0
        
        for transcript in transcripts:
            final_state = transcript.final_state
            mine_positions = set(final_state.mine_positions)
            flagged_positions = set(final_state.flagged_cells)
            
            # Count flags
            total_flags += len(flagged_positions)
            correct_flags += len(mine_positions & flagged_positions)
            
            # Count mines
            total_mines += len(mine_positions)
            flagged_mines += len(mine_positions & flagged_positions)
        
        precision = correct_flags / total_flags if total_flags > 0 else 0.0
        recall = flagged_mines / total_mines if total_mines > 0 else 0.0
        
        return precision, recall
    
    def _calculate_average_moves_to_win(
        self, transcripts: List[GameTranscript]
    ) -> Optional[float]:
        """Calculate average number of moves in winning games."""
        winning_games = [
            t for t in transcripts if t.final_state.status == GameStatus.WON
        ]
        
        if not winning_games:
            return None
        
        total_moves = sum(len(t.moves) for t in winning_games)
        return total_moves / len(winning_games)
    
    def _calculate_average_moves_to_loss(
        self, transcripts: List[GameTranscript]
    ) -> Optional[float]:
        """Calculate average number of moves in losing games."""
        losing_games = [
            t for t in transcripts if t.final_state.status == GameStatus.LOST
        ]
        
        if not losing_games:
            return None
        
        total_moves = sum(len(t.moves) for t in losing_games)
        return total_moves / len(losing_games)
    
    def _calculate_board_coverage_on_loss(
        self, transcripts: List[GameTranscript]
    ) -> float:
        """Calculate average board coverage when games are lost."""
        coverages = []
        
        for transcript in transcripts:
            if transcript.final_state.status == GameStatus.LOST:
                state = transcript.final_state
                total_cells = state.board_rows * state.board_cols
                non_mine_cells = total_cells - len(state.mine_positions)
                revealed_cells = len(state.revealed_cells)
                
                if non_mine_cells > 0:
                    coverage = revealed_cells / non_mine_cells
                    coverages.append(coverage)
        
        return np.mean(coverages) if coverages else 0.0
    
    def _calculate_reasoning_quality(
        self, transcripts: List[GameTranscript]
    ) -> Optional[float]:
        """
        Calculate reasoning quality score.
        
        This is a simplified version - a full implementation might use
        an LLM to evaluate reasoning or check logical consistency.
        """
        total_moves = 0
        moves_with_reasoning = 0
        
        for transcript in transcripts:
            for move in transcript.moves:
                total_moves += 1
                if move.model_reasoning and len(move.model_reasoning) > 20:
                    moves_with_reasoning += 1
        
        if total_moves == 0:
            return None
        
        # For now, just return percentage of moves with reasoning
        # A more sophisticated version would evaluate reasoning quality
        return moves_with_reasoning / total_moves
    
    def calculate_per_game_metrics(
        self, transcript: GameTranscript
    ) -> Dict[str, Any]:
        """
        Calculate metrics for a single game.
        
        Args:
            transcript: Single game transcript
        
        Returns:
            Dictionary of metrics for this game
        """
        state = transcript.final_state
        total_cells = state.board_rows * state.board_cols
        non_mine_cells = total_cells - len(state.mine_positions)
        
        # Calculate valid move rate
        valid_moves = sum(1 for move in transcript.moves if move.was_valid)
        valid_move_rate = valid_moves / len(transcript.moves) if transcript.moves else 0.0
        
        # Calculate mine identification
        mine_positions = set(state.mine_positions)
        flagged_positions = set(state.flagged_cells)
        correct_flags = len(mine_positions & flagged_positions)
        
        flag_precision = (
            correct_flags / len(flagged_positions) 
            if flagged_positions else 0.0
        )
        flag_recall = (
            correct_flags / len(mine_positions)
            if mine_positions else 0.0
        )
        
        # Calculate board coverage
        board_coverage = (
            len(state.revealed_cells) / non_mine_cells
            if non_mine_cells > 0 else 0.0
        )
        
        return {
            "game_id": transcript.game_id,
            "model": transcript.model_name,
            "won": state.status == GameStatus.WON,
            "status": state.status.value,
            "moves": len(transcript.moves),
            "valid_move_rate": valid_move_rate,
            "flag_precision": flag_precision,
            "flag_recall": flag_recall,
            "board_coverage": board_coverage,
            "duration_seconds": transcript.duration_seconds,
        }