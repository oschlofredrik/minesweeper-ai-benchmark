"""Minesweeper board implementation."""

import random
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, field

from src.core.types import Position, CellState
from src.core.exceptions import InvalidBoardConfigError


@dataclass
class Cell:
    """Represents a single cell in the Minesweeper board."""
    has_mine: bool = False
    adjacent_mines: int = 0
    state: CellState = CellState.HIDDEN
    
    @property
    def is_revealed(self) -> bool:
        return self.state == CellState.REVEALED
    
    @property
    def is_flagged(self) -> bool:
        return self.state == CellState.FLAGGED
    
    @property
    def is_hidden(self) -> bool:
        return self.state == CellState.HIDDEN


class TiltsBoard:
    """Minesweeper board with game logic."""
    
    def __init__(
        self,
        rows: int = 9,
        cols: int = 9,
        mines: int = 10,
        seed: Optional[int] = None,
        mine_positions: Optional[List[Position]] = None,
    ):
        """
        Initialize a Minesweeper board.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            mines: Number of mines
            seed: Random seed for reproducibility
            mine_positions: Predefined mine positions (for testing/replay)
        """
        if rows < 1 or cols < 1:
            raise InvalidBoardConfigError("Board must have at least 1 row and 1 column")
        
        if mines < 0 or mines >= rows * cols:
            raise InvalidBoardConfigError(
                f"Invalid number of mines: {mines} (board has {rows * cols} cells)"
            )
        
        self.rows = rows
        self.cols = cols
        self.total_mines = mines
        self.seed = seed
        
        # Initialize board
        self._grid: List[List[Cell]] = [
            [Cell() for _ in range(cols)] for _ in range(rows)
        ]
        
        # Place mines
        if mine_positions:
            self._place_mines_at_positions(mine_positions)
        else:
            self._place_random_mines()
        
        # Calculate adjacent mine counts
        self._calculate_adjacent_mines()
    
    def _place_mines_at_positions(self, positions: List[Position]) -> None:
        """Place mines at specific positions."""
        if len(positions) != self.total_mines:
            raise InvalidBoardConfigError(
                f"Expected {self.total_mines} mine positions, got {len(positions)}"
            )
        
        for pos in positions:
            if not self._is_valid_position(pos):
                raise InvalidBoardConfigError(f"Invalid position: {pos}")
            self._grid[pos.row][pos.col].has_mine = True
    
    def _place_random_mines(self) -> None:
        """Place mines randomly on the board."""
        if self.seed is not None:
            random.seed(self.seed)
        
        # Generate all possible positions
        all_positions = [
            Position(r, c) for r in range(self.rows) for c in range(self.cols)
        ]
        
        # Randomly select mine positions
        mine_positions = random.sample(all_positions, self.total_mines)
        
        for pos in mine_positions:
            self._grid[pos.row][pos.col].has_mine = True
    
    def _calculate_adjacent_mines(self) -> None:
        """Calculate adjacent mine counts for all cells."""
        for row in range(self.rows):
            for col in range(self.cols):
                if not self._grid[row][col].has_mine:
                    count = sum(
                        1 for pos in self._get_neighbors(Position(row, col))
                        if self._grid[pos.row][pos.col].has_mine
                    )
                    self._grid[row][col].adjacent_mines = count
    
    def _get_neighbors(self, pos: Position) -> List[Position]:
        """Get all valid neighbor positions for a given position."""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                new_pos = Position(pos.row + dr, pos.col + dc)
                if self._is_valid_position(new_pos):
                    neighbors.append(new_pos)
        
        return neighbors
    
    def _is_valid_position(self, pos: Position) -> bool:
        """Check if a position is valid on the board."""
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols
    
    def get_cell(self, pos: Position) -> Cell:
        """Get cell at position."""
        if not self._is_valid_position(pos):
            raise InvalidBoardConfigError(f"Invalid position: {pos}")
        return self._grid[pos.row][pos.col]
    
    def reveal_cell(self, pos: Position) -> Tuple[bool, Set[Position]]:
        """
        Reveal a cell and potentially cascade reveal.
        
        Returns:
            Tuple of (hit_mine, revealed_positions)
        """
        if not self._is_valid_position(pos):
            raise InvalidBoardConfigError(f"Invalid position: {pos}")
        
        cell = self._grid[pos.row][pos.col]
        
        # Can't reveal already revealed or flagged cells
        if cell.is_revealed or cell.is_flagged:
            return (False, set())
        
        # Reveal the cell
        cell.state = CellState.REVEALED
        revealed = {pos}
        
        # Check if we hit a mine
        if cell.has_mine:
            return (True, revealed)
        
        # If cell has no adjacent mines, cascade reveal
        if cell.adjacent_mines == 0:
            for neighbor in self._get_neighbors(pos):
                neighbor_cell = self._grid[neighbor.row][neighbor.col]
                if neighbor_cell.is_hidden:
                    _, cascade_revealed = self.reveal_cell(neighbor)
                    revealed.update(cascade_revealed)
        
        return (False, revealed)
    
    def flag_cell(self, pos: Position) -> bool:
        """
        Flag a cell as containing a mine.
        
        Returns:
            True if cell was flagged, False otherwise
        """
        if not self._is_valid_position(pos):
            raise InvalidBoardConfigError(f"Invalid position: {pos}")
        
        cell = self._grid[pos.row][pos.col]
        
        if cell.is_hidden:
            cell.state = CellState.FLAGGED
            return True
        
        return False
    
    def unflag_cell(self, pos: Position) -> bool:
        """
        Remove flag from a cell.
        
        Returns:
            True if flag was removed, False otherwise
        """
        if not self._is_valid_position(pos):
            raise InvalidBoardConfigError(f"Invalid position: {pos}")
        
        cell = self._grid[pos.row][pos.col]
        
        if cell.is_flagged:
            cell.state = CellState.HIDDEN
            return True
        
        return False
    
    def get_game_state(self) -> Dict[str, any]:
        """Get current game state information."""
        hidden_count = 0
        revealed_count = 0
        flagged_count = 0
        correct_flags = 0
        
        for row in self._grid:
            for cell in row:
                if cell.is_hidden:
                    hidden_count += 1
                elif cell.is_revealed:
                    revealed_count += 1
                elif cell.is_flagged:
                    flagged_count += 1
                    if cell.has_mine:
                        correct_flags += 1
        
        # Check win condition: all non-mine cells revealed
        non_mine_cells = self.rows * self.cols - self.total_mines
        is_won = revealed_count == non_mine_cells
        
        return {
            "hidden_cells": hidden_count,
            "revealed_cells": revealed_count,
            "flagged_cells": flagged_count,
            "correct_flags": correct_flags,
            "total_cells": self.rows * self.cols,
            "total_mines": self.total_mines,
            "is_won": is_won,
        }
    
    def to_ascii(self, show_mines: bool = False) -> str:
        """
        Convert board to ASCII representation.
        
        Args:
            show_mines: Whether to show all mines (for debugging/game over)
        
        Returns:
            ASCII string representation of the board
        """
        # Column headers
        lines = ["   " + " ".join(f"{i:2}" for i in range(self.cols))]
        lines.append("   " + "-" * (self.cols * 3))
        
        for row in range(self.rows):
            line_parts = [f"{row:2}|"]
            
            for col in range(self.cols):
                cell = self._grid[row][col]
                
                if show_mines and cell.has_mine:
                    symbol = " *"
                elif cell.is_revealed:
                    if cell.has_mine:
                        symbol = " *"
                    elif cell.adjacent_mines == 0:
                        symbol = " ."
                    else:
                        symbol = f" {cell.adjacent_mines}"
                elif cell.is_flagged:
                    symbol = " F"
                else:  # Hidden
                    symbol = " ?"
                
                line_parts.append(symbol)
            
            lines.append("".join(line_parts))
        
        return "\n".join(lines)
    
    def to_coordinate_list(self) -> Dict[str, List[Dict[str, any]]]:
        """
        Convert board to coordinate list format.
        
        Returns:
            Dictionary with lists of revealed, flagged, and hidden cells
        """
        revealed = []
        flagged = []
        hidden = []
        
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self._grid[row][col]
                pos_dict = {"row": row, "col": col}
                
                if cell.is_revealed:
                    pos_dict["value"] = cell.adjacent_mines if not cell.has_mine else -1
                    revealed.append(pos_dict)
                elif cell.is_flagged:
                    flagged.append(pos_dict)
                else:
                    hidden.append(pos_dict)
        
        return {
            "board_size": {"rows": self.rows, "cols": self.cols},
            "revealed": revealed,
            "flagged": flagged,
            "hidden": hidden,
            "total_mines": self.total_mines,
        }
    
    def get_mine_positions(self) -> List[Position]:
        """Get all mine positions (for debugging/validation)."""
        positions = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self._grid[row][col].has_mine:
                    positions.append(Position(row, col))
        return positions