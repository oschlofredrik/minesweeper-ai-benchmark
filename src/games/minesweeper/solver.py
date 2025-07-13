"""Minesweeper solver for validating solvability and finding safe moves."""

from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from src.core.types import Position, Action, ActionType
from .board import MinesweeperBoard, Cell


@dataclass
class Constraint:
    """Represents a constraint for a set of cells."""
    cells: Set[Position]
    mine_count: int
    
    def __hash__(self) -> int:
        return hash((frozenset(self.cells), self.mine_count))


class MinesweeperSolver:
    """Solver for Minesweeper using constraint satisfaction."""
    
    def __init__(self, board: MinesweeperBoard):
        """Initialize solver with a board."""
        self.board = board
        self.constraints: Set[Constraint] = set()
        self.known_mines: Set[Position] = set()
        self.known_safe: Set[Position] = set()
    
    def find_safe_moves(self) -> List[Action]:
        """
        Find all guaranteed safe moves in the current board state.
        
        Returns:
            List of safe reveal actions
        """
        self._update_constraints()
        self._solve_constraints()
        
        safe_moves = []
        for pos in self.known_safe:
            cell = self.board.get_cell(pos)
            if cell.is_hidden and not cell.is_flagged:
                safe_moves.append(Action(ActionType.REVEAL, pos))
        
        return safe_moves
    
    def find_mine_positions(self) -> List[Position]:
        """
        Find all guaranteed mine positions.
        
        Returns:
            List of positions that definitely contain mines
        """
        self._update_constraints()
        self._solve_constraints()
        
        return list(self.known_mines)
    
    def get_probabilities(self) -> Dict[Position, float]:
        """
        Calculate mine probabilities for all hidden cells.
        
        Returns:
            Dictionary mapping positions to mine probability
        """
        self._update_constraints()
        self._solve_constraints()
        
        probabilities = {}
        
        # Known mines have probability 1.0
        for pos in self.known_mines:
            cell = self.board.get_cell(pos)
            if cell.is_hidden:
                probabilities[pos] = 1.0
        
        # Known safe cells have probability 0.0
        for pos in self.known_safe:
            cell = self.board.get_cell(pos)
            if cell.is_hidden:
                probabilities[pos] = 0.0
        
        # For other cells, use simple heuristic
        # (More sophisticated probability calculation could be added)
        remaining_mines = self.board.total_mines - len(self.known_mines)
        remaining_cells = sum(
            1 for row in range(self.board.rows)
            for col in range(self.board.cols)
            if self.board.get_cell(Position(row, col)).is_hidden
            and Position(row, col) not in self.known_mines
            and Position(row, col) not in self.known_safe
        )
        
        if remaining_cells > 0:
            default_prob = remaining_mines / remaining_cells
            
            for row in range(self.board.rows):
                for col in range(self.board.cols):
                    pos = Position(row, col)
                    cell = self.board.get_cell(pos)
                    if cell.is_hidden and pos not in probabilities:
                        probabilities[pos] = default_prob
        
        return probabilities
    
    def _update_constraints(self) -> None:
        """Update constraints based on current board state."""
        self.constraints.clear()
        self.known_mines.clear()
        self.known_safe.clear()
        
        # Create constraints from revealed cells
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                pos = Position(row, col)
                cell = self.board.get_cell(pos)
                
                if cell.is_revealed and not cell.has_mine:
                    # Get hidden neighbors
                    hidden_neighbors = set()
                    flagged_neighbors = 0
                    
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            
                            neighbor_pos = Position(row + dr, col + dc)
                            if (0 <= neighbor_pos.row < self.board.rows and
                                0 <= neighbor_pos.col < self.board.cols):
                                neighbor_cell = self.board.get_cell(neighbor_pos)
                                
                                if neighbor_cell.is_hidden:
                                    hidden_neighbors.add(neighbor_pos)
                                elif neighbor_cell.is_flagged:
                                    flagged_neighbors += 1
                    
                    if hidden_neighbors:
                        # Create constraint for hidden neighbors
                        remaining_mines = cell.adjacent_mines - flagged_neighbors
                        constraint = Constraint(hidden_neighbors, remaining_mines)
                        self.constraints.add(constraint)
    
    def _solve_constraints(self) -> None:
        """Solve constraints to find known mines and safe cells."""
        changed = True
        
        while changed:
            changed = False
            
            # Process each constraint
            for constraint in list(self.constraints):
                # Skip if no cells in constraint
                if not constraint.cells:
                    continue
                
                # Remove known mines and safe cells from constraint
                remaining_cells = constraint.cells - self.known_mines - self.known_safe
                remaining_mines = constraint.mine_count - len(
                    constraint.cells & self.known_mines
                )
                
                if not remaining_cells:
                    continue
                
                # All remaining cells are mines
                if remaining_mines == len(remaining_cells):
                    self.known_mines.update(remaining_cells)
                    changed = True
                
                # No remaining mines, all cells are safe
                elif remaining_mines == 0:
                    self.known_safe.update(remaining_cells)
                    changed = True
            
            # Try subset reduction
            if not changed:
                changed = self._reduce_constraints()
    
    def _reduce_constraints(self) -> bool:
        """
        Reduce constraints by finding subset relationships.
        
        Returns:
            True if any reduction was made
        """
        constraints_list = list(self.constraints)
        
        for i, c1 in enumerate(constraints_list):
            for j, c2 in enumerate(constraints_list):
                if i >= j:
                    continue
                
                # Check if c1 is subset of c2
                if c1.cells.issubset(c2.cells):
                    # Create new constraint
                    new_cells = c2.cells - c1.cells
                    new_mines = c2.mine_count - c1.mine_count
                    
                    if new_cells and 0 <= new_mines <= len(new_cells):
                        new_constraint = Constraint(new_cells, new_mines)
                        if new_constraint not in self.constraints:
                            self.constraints.add(new_constraint)
                            return True
                
                # Check if c2 is subset of c1
                elif c2.cells.issubset(c1.cells):
                    # Create new constraint
                    new_cells = c1.cells - c2.cells
                    new_mines = c1.mine_count - c2.mine_count
                    
                    if new_cells and 0 <= new_mines <= len(new_cells):
                        new_constraint = Constraint(new_cells, new_mines)
                        if new_constraint not in self.constraints:
                            self.constraints.add(new_constraint)
                            return True
        
        return False
    
    def is_solvable_without_guessing(self) -> bool:
        """
        Check if the current board state can be solved without guessing.
        
        Returns:
            True if there's always at least one safe move available
        """
        # This is a simplified check - full solvability analysis would require
        # simulating all possible game paths
        safe_moves = self.find_safe_moves()
        return len(safe_moves) > 0