"""MineBench evaluation metrics implementation."""
import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict

class MineBenchMetrics:
    """Calculate MineBench evaluation metrics for Minesweeper."""
    
    @staticmethod
    def calculate_win_rate(games: List[Dict[str, Any]]) -> Tuple[float, float, float]:
        """Calculate win rate with Wilson confidence interval.
        
        Returns:
            (win_rate, lower_bound, upper_bound)
        """
        if not games:
            return 0.0, 0.0, 0.0
            
        wins = sum(1 for g in games if g.get('won', False))
        n = len(games)
        
        if n == 0:
            return 0.0, 0.0, 0.0
            
        p_hat = wins / n
        
        # Wilson score interval with 95% confidence
        z = 1.96  # 95% confidence
        
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
        
        lower = max(0, center - margin)
        upper = min(1, center + margin)
        
        return p_hat, lower, upper
    
    @staticmethod
    def calculate_valid_move_rate(games: List[Dict[str, Any]]) -> float:
        """Calculate the rate of valid moves across all games."""
        total_moves = 0
        valid_moves = 0
        
        for game in games:
            moves = game.get('moves', [])
            total_moves += len(moves)
            valid_moves += sum(1 for m in moves if m.get('valid', False))
        
        return valid_moves / total_moves if total_moves > 0 else 0.0
    
    @staticmethod
    def calculate_mine_identification_metrics(games: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate mine identification precision and recall."""
        total_mines = 0
        correctly_identified = 0
        total_flags = 0
        
        for game in games:
            mines = game.get('mines_total', 0)
            identified = game.get('mines_identified', 0)
            false_flags = game.get('false_flags', 0)
            
            total_mines += mines
            correctly_identified += identified
            total_flags += identified + false_flags
        
        precision = correctly_identified / total_flags if total_flags > 0 else 0.0
        recall = correctly_identified / total_mines if total_mines > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    @staticmethod
    def calculate_board_coverage(games: List[Dict[str, Any]]) -> float:
        """Calculate average board coverage (percentage of safe cells revealed)."""
        total_coverage = 0
        count = 0
        
        for game in games:
            coverage = game.get('coverage_ratio', 0.0)
            if coverage > 0:
                total_coverage += coverage
                count += 1
        
        return total_coverage / count if count > 0 else 0.0
    
    @staticmethod
    def calculate_ms_scores(games: List[Dict[str, Any]], subset: str = 'standard') -> Dict[str, float]:
        """Calculate MineBench MS-S and MS-I scores.
        
        Args:
            games: List of completed games
            subset: 'standard' or 'intermediate'
            
        Returns:
            Dictionary with MS-S and MS-I scores
        """
        # Filter games by subset if needed
        if subset == 'standard':
            # Standard subset: easier difficulties
            filtered_games = [g for g in games if g.get('difficulty') in ['easy', 'medium']]
        else:
            # Intermediate subset: harder difficulties
            filtered_games = [g for g in games if g.get('difficulty') in ['hard', 'expert']]
        
        if not filtered_games:
            return {'MS-S': 0.0, 'MS-I': 0.0}
        
        # Calculate component metrics
        win_rate, _, _ = MineBenchMetrics.calculate_win_rate(filtered_games)
        valid_rate = MineBenchMetrics.calculate_valid_move_rate(filtered_games)
        mine_metrics = MineBenchMetrics.calculate_mine_identification_metrics(filtered_games)
        coverage = MineBenchMetrics.calculate_board_coverage(filtered_games)
        
        # MS-S: Standard score (focuses on win rate and valid moves)
        ms_s = (
            0.4 * win_rate +
            0.3 * valid_rate +
            0.2 * mine_metrics['precision'] +
            0.1 * coverage
        )
        
        # MS-I: Intermediate score (focuses on mine identification)
        ms_i = (
            0.3 * win_rate +
            0.2 * valid_rate +
            0.3 * mine_metrics['f1_score'] +
            0.2 * coverage
        )
        
        return {
            'MS-S': round(ms_s, 4),
            'MS-I': round(ms_i, 4),
            'win_rate': round(win_rate, 4),
            'valid_move_rate': round(valid_rate, 4),
            'mine_precision': round(mine_metrics['precision'], 4),
            'mine_recall': round(mine_metrics['recall'], 4),
            'mine_f1': round(mine_metrics['f1_score'], 4),
            'coverage': round(coverage, 4)
        }
    
    @staticmethod
    def calculate_reasoning_score(games: List[Dict[str, Any]], llm_judge_results: List[Dict[str, Any]] = None) -> float:
        """Calculate reasoning quality score using LLM judge results."""
        if not llm_judge_results:
            # Fallback: analyze reasoning length and structure
            total_score = 0
            count = 0
            
            for game in games:
                moves = game.get('moves', [])
                for move in moves:
                    reasoning = move.get('reasoning', '')
                    if reasoning:
                        # Simple heuristic: longer, structured reasoning is better
                        score = min(1.0, len(reasoning) / 200)  # Cap at 200 chars
                        if any(word in reasoning.lower() for word in ['because', 'since', 'therefore', 'thus']):
                            score = min(1.0, score + 0.2)
                        total_score += score
                        count += 1
            
            return total_score / count if count > 0 else 0.0
        
        # Use LLM judge results if available
        total_score = sum(r.get('score', 0) for r in llm_judge_results)
        return total_score / len(llm_judge_results) if llm_judge_results else 0.0


class RiskMetrics:
    """Calculate evaluation metrics for Risk game."""
    
    @staticmethod
    def calculate_territory_control(games: List[Dict[str, Any]]) -> float:
        """Calculate average territory control percentage."""
        total_control = 0
        count = 0
        
        for game in games:
            control = game.get('territory_control', 0.0)
            if control > 0:
                total_control += control
                count += 1
        
        return total_control / count if count > 0 else 0.0
    
    @staticmethod
    def calculate_strategic_score(games: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate strategic performance metrics for Risk."""
        wins = sum(1 for g in games if g.get('won', False))
        total_games = len(games) if games else 1
        
        avg_territories = sum(g.get('territory_control', 0) for g in games) / total_games
        avg_armies = sum(g.get('total_armies', 0) for g in games) / total_games
        
        # Strategic score combines win rate and territorial control
        strategic_score = (0.6 * (wins / total_games) + 0.4 * avg_territories)
        
        return {
            'win_rate': wins / total_games,
            'avg_territory_control': avg_territories,
            'avg_army_strength': avg_armies,
            'strategic_score': round(strategic_score, 4)
        }