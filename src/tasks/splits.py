"""Data split management for public/hidden task splits."""

import random
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import json
import hashlib

from src.core.types import Task, TaskType, Difficulty


class DataSplitManager:
    """Manages public and hidden splits for benchmark tasks."""
    
    PUBLIC_SPLIT_RATIO = 0.8  # 80% public, 20% hidden
    
    def __init__(self, splits_dir: Optional[Path] = None):
        """
        Initialize data split manager.
        
        Args:
            splits_dir: Directory for storing split information
        """
        self.splits_dir = splits_dir or Path("data/splits")
        self.splits_dir.mkdir(parents=True, exist_ok=True)
        
        self.splits_file = self.splits_dir / "task_splits.json"
        self.splits_data = self._load_splits()
    
    def create_splits(
        self,
        tasks: List[Task],
        seed: int = 42,
        force: bool = False,
    ) -> Tuple[List[Task], List[Task]]:
        """
        Create public and hidden splits from tasks.
        
        Args:
            tasks: All tasks to split
            seed: Random seed for reproducibility
            force: Force recreation of splits
        
        Returns:
            Tuple of (public_tasks, hidden_tasks)
        """
        # Check if splits already exist
        if not force and self.splits_data:
            return self._apply_existing_splits(tasks)
        
        # Create new splits
        random.seed(seed)
        task_ids = [task.task_id for task in tasks]
        random.shuffle(task_ids)
        
        split_point = int(len(task_ids) * self.PUBLIC_SPLIT_RATIO)
        public_ids = set(task_ids[:split_point])
        hidden_ids = set(task_ids[split_point:])
        
        # Save splits
        self.splits_data = {
            "public": list(public_ids),
            "hidden": list(hidden_ids),
            "seed": seed,
            "created_at": str(Path.ctime(Path())),
        }
        self._save_splits()
        
        # Apply splits
        public_tasks = [t for t in tasks if t.task_id in public_ids]
        hidden_tasks = [t for t in tasks if t.task_id in hidden_ids]
        
        return public_tasks, hidden_tasks
    
    def get_task_split(self, task_id: str) -> str:
        """
        Get split assignment for a task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            "public", "hidden", or "unknown"
        """
        if task_id in self.splits_data.get("public", []):
            return "public"
        elif task_id in self.splits_data.get("hidden", []):
            return "hidden"
        else:
            return "unknown"
    
    def filter_by_split(
        self,
        tasks: List[Task],
        split: str = "public",
    ) -> List[Task]:
        """
        Filter tasks by split assignment.
        
        Args:
            tasks: Tasks to filter
            split: "public" or "hidden"
        
        Returns:
            Filtered tasks
        """
        if split not in ["public", "hidden"]:
            raise ValueError(f"Invalid split: {split}")
        
        split_ids = set(self.splits_data.get(split, []))
        return [t for t in tasks if t.task_id in split_ids]
    
    def get_hidden_answers(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Get answers for hidden split tasks.
        
        Args:
            tasks: Hidden split tasks
        
        Returns:
            Dictionary of task_id -> answer
        """
        answers = {}
        hidden_ids = set(self.splits_data.get("hidden", []))
        
        for task in tasks:
            if task.task_id in hidden_ids:
                # Extract answer based on task type
                if task.task_type == TaskType.STATIC:
                    solution = task.board_config.get("solution", {})
                    safe_moves = solution.get("safe_moves", [])
                    if safe_moves:
                        answers[task.task_id] = safe_moves[0]  # First safe move
                else:
                    # For interactive tasks, store board seed
                    answers[task.task_id] = {
                        "seed": task.board_config.get("seed"),
                        "type": "interactive",
                    }
        
        return answers
    
    def mask_hidden_solutions(self, tasks: List[Task]) -> List[Task]:
        """
        Remove solutions from hidden split tasks.
        
        Args:
            tasks: Tasks to process
        
        Returns:
            Tasks with hidden solutions masked
        """
        hidden_ids = set(self.splits_data.get("hidden", []))
        masked_tasks = []
        
        for task in tasks:
            if task.task_id in hidden_ids:
                # Create copy without solution
                masked_config = task.board_config.copy()
                masked_config.pop("solution", None)
                
                masked_task = Task(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    difficulty=task.difficulty,
                    board_config=masked_config,
                    description=task.description,
                    metadata=task.metadata,
                    created_at=task.created_at,
                )
                masked_tasks.append(masked_task)
            else:
                masked_tasks.append(task)
        
        return masked_tasks
    
    def _load_splits(self) -> Dict[str, Any]:
        """Load existing splits from file."""
        if self.splits_file.exists():
            with open(self.splits_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_splits(self) -> None:
        """Save splits to file."""
        with open(self.splits_file, "w") as f:
            json.dump(self.splits_data, f, indent=2)
    
    def _apply_existing_splits(
        self, tasks: List[Task]
    ) -> Tuple[List[Task], List[Task]]:
        """Apply existing splits to tasks."""
        public_ids = set(self.splits_data.get("public", []))
        hidden_ids = set(self.splits_data.get("hidden", []))
        
        public_tasks = [t for t in tasks if t.task_id in public_ids]
        hidden_tasks = [t for t in tasks if t.task_id in hidden_ids]
        
        # Handle new tasks not in splits
        new_tasks = [
            t for t in tasks
            if t.task_id not in public_ids and t.task_id not in hidden_ids
        ]
        
        if new_tasks:
            # Add new tasks to public split by default
            for task in new_tasks:
                public_tasks.append(task)
                self.splits_data["public"].append(task.task_id)
            self._save_splits()
        
        return public_tasks, hidden_tasks


class HiddenAnswerValidator:
    """Validates answers against hidden split ground truth."""
    
    def __init__(self, answers: Dict[str, Any]):
        """
        Initialize validator with hidden answers.
        
        Args:
            answers: Hidden split answers
        """
        self.answers = answers
    
    def validate(self, task_id: str, prediction: str) -> bool:
        """
        Validate a prediction against hidden answer.
        
        Args:
            task_id: Task identifier
            prediction: Model's prediction
        
        Returns:
            Whether prediction is correct
        """
        if task_id not in self.answers:
            return False
        
        answer = self.answers[task_id]
        
        # Handle different answer formats
        if isinstance(answer, dict):
            # Complex answer (e.g., for interactive tasks)
            return self._validate_complex(prediction, answer)
        else:
            # Simple answer comparison
            return self._normalize_answer(prediction) == self._normalize_answer(str(answer))
    
    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for comparison."""
        # Remove whitespace and convert to lowercase
        normalized = answer.strip().lower()
        
        # Handle coordinate formats
        # "reveal (2, 3)" -> "reveal 2 3"
        normalized = normalized.replace("(", "").replace(")", "").replace(",", "")
        
        return normalized
    
    def _validate_complex(self, prediction: str, answer: Dict[str, Any]) -> bool:
        """Validate complex answers."""
        # For interactive tasks, we can't validate individual moves
        # Return True if it's marked as interactive
        return answer.get("type") == "interactive"