"""Centralized prompt management for the Minesweeper AI Benchmark."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""
    id: str
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    supports_function_calling: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = None
    
    def format_user_prompt(self, board_state: str, **kwargs) -> str:
        """Format the user prompt with the given board state."""
        return self.user_prompt_template.format(board_state=board_state, **kwargs)


class PromptManager:
    """Manages prompt templates for different scenarios."""
    
    def __init__(self, prompts_dir: str = "data/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Load default prompt templates."""
        # Standard prompt (without function calling)
        self._templates["standard"] = PromptTemplate(
            id="standard",
            name="Standard Prompt",
            description="Basic prompt for text-based responses",
            system_prompt="You are an expert Minesweeper player. Analyze the board carefully and make logical deductions. You MUST ALWAYS provide an action. Even if you're uncertain, choose the move with the highest probability of success. Never respond without an action.",
            user_prompt_template="""You are playing Minesweeper. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines
- *: Mine (only shown when game is over)

Based on logical deduction, what is your next move?

IMPORTANT: You MUST provide exactly one action in this format:
Action: [reveal/flag/unflag] (row, col)

Where:
- reveal: Uncover a hidden cell
- flag: Mark a cell as containing a mine
- unflag: Remove a flag from a cell
- row, col: 0-based coordinates

Example: Action: reveal (2, 3)

Explain your reasoning step by step, then provide your action at the end.

Remember: Even if you're unsure, you MUST choose an action. If no moves seem certain, choose the cell with the highest probability of being safe.""",
            supports_function_calling=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Function calling prompt
        self._templates["function_calling"] = PromptTemplate(
            id="function_calling",
            name="Function Calling Prompt",
            description="Prompt optimized for function calling/tool use",
            system_prompt="""You are an expert Minesweeper player with access to a make_move function.

Your task is to analyze the board and make the best possible move using logical deduction.

IMPORTANT: Follow these steps:
1. First, think step-by-step and write your logical analysis of the board
2. Then, call the make_move function with your chosen action

The make_move function takes:
- action: "reveal", "flag", or "unflag"
- row: 0-based row index
- col: 0-based column index
- reasoning: Brief summary of why this move (can be shorter than your analysis)

You MUST call the make_move function after your analysis. Both your detailed reasoning and the function call will be captured.""",
            user_prompt_template="""Current Minesweeper board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Please analyze the board step-by-step:
1. Identify revealed numbers and their adjacent cells
2. Count flagged mines around each number
3. Determine which cells must be mines or must be safe
4. Explain your logical deductions

After your analysis, use the make_move function to execute your chosen move.""",
            supports_function_calling=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Chain of thought prompt
        self._templates["cot"] = PromptTemplate(
            id="cot",
            name="Chain of Thought",
            description="Detailed reasoning with step-by-step analysis",
            system_prompt="You are an expert Minesweeper player. Break down your analysis into clear steps. You MUST always conclude with a specific action in the required format.",
            user_prompt_template="""You are an expert Minesweeper player. Analyze this board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)  
- 1-8: Number of adjacent mines

Let's think step by step:
1. First, identify all revealed numbers and their adjacent hidden cells
2. Count how many mines are already flagged around each number
3. Determine which cells must be mines or must be safe
4. Choose the best move based on certainty

After your analysis, you MUST provide exactly one action in this format:
Action: [reveal/flag/unflag] (row, col)

Where row and col are 0-based coordinates.
Example: Action: reveal (2, 3)

Remember: You MUST always provide an action, even if uncertain.""",
            supports_function_calling=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Reasoning model prompt
        self._templates["reasoning"] = PromptTemplate(
            id="reasoning",
            name="Reasoning Model Prompt",
            description="Optimized for models with extended reasoning capabilities",
            system_prompt="You are an expert Minesweeper player. Provide thorough logical analysis. You MUST always conclude with a specific action in the required format.",
            user_prompt_template="""You are an expert Minesweeper player. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Analyze the board carefully. Think through all the logical deductions you can make based on the revealed numbers and their adjacent cells. Consider which cells must be mines and which must be safe.

IMPORTANT: After your analysis, you MUST provide exactly one action in this format:
Action: [reveal/flag/unflag] (row, col)

Where row and col are 0-based coordinates.
Example: Action: reveal (2, 3)

Remember: You MUST always provide an action. If no moves seem certain, choose the cell with the highest probability of being safe.""",
            supports_function_calling=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Simple direct prompt
        self._templates["simple"] = PromptTemplate(
            id="simple",
            name="Simple Direct Prompt",
            description="Very direct prompt that focuses on always getting an action",
            system_prompt="You are playing Minesweeper. You must ALWAYS provide an action in the exact format specified.",
            user_prompt_template="""Current Minesweeper board:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (no adjacent mines)
- 1-8: Number of adjacent mines

Analyze the board and choose your next move.

YOU MUST provide your action in EXACTLY this format:
Action: reveal (row, col)
OR
Action: flag (row, col)
OR
Action: unflag (row, col)

The row and col are 0-based coordinates.

Example valid responses:
- "I think cell (2,3) is safe. Action: reveal (2, 3)"
- "This must be a mine. Action: flag (0, 1)"

IMPORTANT: You MUST include "Action:" followed by the command. No other format will be accepted.""",
            supports_function_calling=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID."""
        return self._templates.get(template_id)
    
    def list_templates(self) -> Dict[str, PromptTemplate]:
        """List all available templates."""
        return self._templates.copy()
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add or update a prompt template."""
        self._templates[template.id] = template
        self._save_template(template)
    
    def _save_template(self, template: PromptTemplate) -> None:
        """Save a template to disk."""
        filepath = self.prompts_dir / f"{template.id}.json"
        data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt_template": template.user_prompt_template,
            "supports_function_calling": template.supports_function_calling,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "is_active": template.is_active,
            "metadata": template.metadata or {}
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_disk(self) -> None:
        """Load all templates from disk."""
        for filepath in self.prompts_dir.glob("*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                template = PromptTemplate(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    system_prompt=data["system_prompt"],
                    user_prompt_template=data["user_prompt_template"],
                    supports_function_calling=data["supports_function_calling"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    is_active=data.get("is_active", True),
                    metadata=data.get("metadata", {})
                )
                self._templates[template.id] = template
            except Exception as e:
                print(f"Error loading template from {filepath}: {e}")
    
    def get_prompt_for_model(
        self,
        model_type: str,
        board_state: str,
        use_function_calling: bool = True
    ) -> Dict[str, str]:
        """Get the appropriate prompts for a model."""
        if use_function_calling and model_type in ["openai", "anthropic"]:
            template = self.get_template("function_calling")
        else:
            template = self.get_template("standard")
        
        if not template:
            template = self.get_template("standard")
        
        return {
            "system": template.system_prompt,
            "user": template.format_user_prompt(board_state)
        }


# Global instance
prompt_manager = PromptManager()