"""Task repository for managing benchmark tasks."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid

from src.core.types import Task, TaskType, Difficulty


class TaskRepository:
    """Repository for storing and retrieving benchmark tasks."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize task repository.
        
        Args:
            data_dir: Directory for storing tasks
        """
        self.data_dir = data_dir or Path("data/tasks")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        self.interactive_dir = self.data_dir / "interactive"
        self.static_dir = self.data_dir / "static"
        self.interactive_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
    
    def save_task(self, task: Task) -> None:
        """
        Save a task to the repository.
        
        Args:
            task: Task to save
        """
        # Determine directory based on task type
        if task.task_type == TaskType.INTERACTIVE:
            task_dir = self.interactive_dir
        else:
            task_dir = self.static_dir
        
        # Create filename
        filename = f"{task.difficulty.value}_{task.task_id}.json"
        filepath = task_dir / filename
        
        # Convert task to dict
        task_dict = self._task_to_dict(task)
        
        # Save to file
        with open(filepath, "w") as f:
            json.dump(task_dict, f, indent=2)
    
    def save_tasks(self, tasks: List[Task]) -> None:
        """Save multiple tasks."""
        for task in tasks:
            self.save_task(task)
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """
        Load a task by ID.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task or None if not found
        """
        # Search in both directories
        for task_dir in [self.interactive_dir, self.static_dir]:
            for filepath in task_dir.glob(f"*_{task_id}.json"):
                with open(filepath, "r") as f:
                    task_dict = json.load(f)
                return self._dict_to_task(task_dict)
        
        return None
    
    def load_tasks(
        self,
        task_type: Optional[TaskType] = None,
        difficulty: Optional[Difficulty] = None,
        limit: Optional[int] = None,
    ) -> List[Task]:
        """
        Load tasks with optional filtering.
        
        Args:
            task_type: Filter by task type
            difficulty: Filter by difficulty
            limit: Maximum number of tasks to load
        
        Returns:
            List of tasks
        """
        tasks = []
        
        # Determine directories to search
        if task_type == TaskType.INTERACTIVE:
            search_dirs = [self.interactive_dir]
        elif task_type == TaskType.STATIC:
            search_dirs = [self.static_dir]
        else:
            search_dirs = [self.interactive_dir, self.static_dir]
        
        # Load tasks
        for task_dir in search_dirs:
            for filepath in task_dir.glob("*.json"):
                if difficulty and not filepath.name.startswith(difficulty.value):
                    continue
                
                with open(filepath, "r") as f:
                    task_dict = json.load(f)
                
                task = self._dict_to_task(task_dict)
                tasks.append(task)
                
                if limit and len(tasks) >= limit:
                    return tasks
        
        return tasks
    
    def get_task_count(
        self,
        task_type: Optional[TaskType] = None,
        difficulty: Optional[Difficulty] = None,
    ) -> int:
        """Get count of tasks matching criteria."""
        tasks = self.load_tasks(task_type, difficulty)
        return len(tasks)
    
    def clear_tasks(
        self,
        task_type: Optional[TaskType] = None,
        difficulty: Optional[Difficulty] = None,
    ) -> int:
        """
        Clear tasks matching criteria.
        
        Returns:
            Number of tasks deleted
        """
        count = 0
        
        # Determine directories to search
        if task_type == TaskType.INTERACTIVE:
            search_dirs = [self.interactive_dir]
        elif task_type == TaskType.STATIC:
            search_dirs = [self.static_dir]
        else:
            search_dirs = [self.interactive_dir, self.static_dir]
        
        # Delete matching files
        for task_dir in search_dirs:
            for filepath in task_dir.glob("*.json"):
                if difficulty and not filepath.name.startswith(difficulty.value):
                    continue
                
                filepath.unlink()
                count += 1
        
        return count
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "difficulty": task.difficulty.value,
            "board_config": task.board_config,
            "description": task.description,
            "metadata": task.metadata,
            "created_at": task.created_at.isoformat(),
        }
    
    def _dict_to_task(self, data: Dict[str, Any]) -> Task:
        """Convert dictionary to task."""
        return Task(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            difficulty=Difficulty(data["difficulty"]),
            board_config=data["board_config"],
            description=data["description"],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
        )
    
    def create_default_tasks(self) -> None:
        """Create a default set of benchmark tasks."""
        from .generator import TaskGenerator
        
        generator = TaskGenerator()
        
        # Generate tasks for each difficulty
        for difficulty in Difficulty:
            # Interactive tasks
            interactive_tasks = generator.generate_task_batch(
                num_tasks=10,
                task_type=TaskType.INTERACTIVE,
                difficulty=difficulty,
            )
            self.save_tasks(interactive_tasks)
            
            # Static tasks
            static_tasks = generator.generate_task_batch(
                num_tasks=10,
                task_type=TaskType.STATIC,
                difficulty=difficulty,
            )
            self.save_tasks(static_tasks)
        
        print(f"Created {self.get_task_count()} default tasks")