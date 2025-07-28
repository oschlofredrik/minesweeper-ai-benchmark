"""Prompt template management and versioning."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import hashlib


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""
    name: str
    template: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    few_shot_examples: List[Dict[str, str]] = field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def hash(self) -> str:
        """Generate hash of template content."""
        content = self.template + str(self.few_shot_examples)
        return hashlib.sha256(content.encode()).hexdigest()[:8]
    
    def format(self, **kwargs) -> str:
        """Format template with provided values."""
        # Apply default parameters
        format_args = self.parameters.copy()
        format_args.update(kwargs)
        
        # Format template
        formatted = self.template.format(**format_args)
        
        # Add few-shot examples if provided
        if self.few_shot_examples:
            examples_text = "\n\nExamples:\n"
            for i, example in enumerate(self.few_shot_examples, 1):
                examples_text += f"\nExample {i}:\n"
                examples_text += f"Board:\n{example.get('board', '')}\n"
                examples_text += f"Action: {example.get('action', '')}\n"
                if example.get('reasoning'):
                    examples_text += f"Reasoning: {example.get('reasoning', '')}\n"
            
            formatted = examples_text + "\n" + formatted
        
        return formatted


class PromptManager:
    """Manages prompt templates and variations."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Directory for storing prompt templates
        """
        self.prompts_dir = prompts_dir or Path("data/prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
        self._load_custom_templates()
    
    def _load_builtin_templates(self) -> None:
        """Load built-in prompt templates."""
        # Standard prompt
        self.templates["standard"] = PromptTemplate(
            name="standard",
            template="""You are playing Minesweeper. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines
- *: Mine (only shown when game is over)

Based on logical deduction, what is your next move? Please provide:
1. Your reasoning for the move
2. Your action in the format: "Action: [reveal/flag/unflag] (row, col)"

Think step by step about which cells are definitely safe or definitely mines based on the numbers shown.""",
            description="Standard prompt with clear instructions",
            parameters={"board_state": ""},
            tags=["basic", "clear"],
        )
        
        # Chain of thought prompt
        self.templates["chain_of_thought"] = PromptTemplate(
            name="chain_of_thought",
            template="""You are an expert Minesweeper player. Analyze this board state step by step:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Let's think through this methodically:
1. First, identify all revealed numbers and count their adjacent hidden cells
2. For each number, count how many mines are already flagged nearby
3. Determine which cells MUST be mines (when a number's requirement is exactly met by hidden cells)
4. Determine which cells MUST be safe (when a number's mine requirement is already satisfied by flags)
5. If no certain moves exist, identify the safest probabilistic move

Work through your reasoning step by step, then provide your move as:
Action: [reveal/flag] (row, col)""",
            description="Enhanced chain-of-thought reasoning",
            parameters={"board_state": ""},
            tags=["cot", "detailed"],
        )
        
        # Structured output prompt
        self.templates["structured"] = PromptTemplate(
            name="structured",
            template="""Analyze this Minesweeper board and provide your move in JSON format:

{board_state}

Legend: ?: hidden, F: flag, .: empty, 1-8: adjacent mines

Respond with JSON only:
{{
    "analysis": {{
        "safe_cells": [[row, col], ...],
        "mine_cells": [[row, col], ...],
        "key_deductions": ["reasoning 1", "reasoning 2", ...]
    }},
    "action": {{
        "type": "reveal|flag",
        "position": [row, col],
        "confidence": 0.0-1.0
    }},
    "reasoning": "Brief explanation of why this move was chosen"
}}""",
            description="Structured JSON output format",
            parameters={"board_state": ""},
            tags=["json", "structured"],
        )
        
        # Pattern recognition prompt
        self.templates["pattern_based"] = PromptTemplate(
            name="pattern_based",
            template="""You are a Minesweeper expert who recognizes common patterns. Analyze this board:

{board_state}

Look for these common patterns:
- 1-2-1 pattern: Middle cell is safe
- Corner patterns: Numbers in corners often have deterministic solutions  
- Edge constraints: Numbers on edges have fewer neighbors
- Completing numbers: When a number has exactly the right amount of hidden neighbors

{pattern_hints}

Identify any patterns you see, then make your move:
Action: [reveal/flag] (row, col)""",
            description="Pattern-recognition focused prompt",
            parameters={
                "board_state": "",
                "pattern_hints": "Focus on finding guaranteed safe moves from patterns."
            },
            tags=["patterns", "advanced"],
        )
    
    def _load_custom_templates(self) -> None:
        """Load custom templates from disk."""
        for file in self.prompts_dir.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                
                template = PromptTemplate(
                    name=data["name"],
                    template=data["template"],
                    description=data.get("description", ""),
                    parameters=data.get("parameters", {}),
                    few_shot_examples=data.get("few_shot_examples", []),
                    version=data.get("version", "1.0"),
                    tags=data.get("tags", []),
                    performance_metrics=data.get("performance_metrics", {}),
                )
                
                self.templates[template.name] = template
                
            except Exception as e:
                print(f"Error loading template from {file}: {e}")
    
    def save_template(self, template: PromptTemplate) -> None:
        """Save a template to disk."""
        self.templates[template.name] = template
        
        filepath = self.prompts_dir / f"{template.name}.json"
        
        data = {
            "name": template.name,
            "template": template.template,
            "description": template.description,
            "parameters": template.parameters,
            "few_shot_examples": template.few_shot_examples,
            "version": template.version,
            "created_at": template.created_at.isoformat(),
            "tags": template.tags,
            "performance_metrics": template.performance_metrics,
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self, tags: Optional[List[str]] = None) -> List[PromptTemplate]:
        """
        List all templates, optionally filtered by tags.
        
        Args:
            tags: Filter templates by tags
        
        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        return templates
    
    def create_variation(
        self,
        base_template: str,
        name: str,
        modifications: Dict[str, Any],
    ) -> PromptTemplate:
        """
        Create a variation of an existing template.
        
        Args:
            base_template: Name of base template
            name: Name for new variation
            modifications: Changes to apply
        
        Returns:
            New template variation
        """
        base = self.get_template(base_template)
        if not base:
            raise ValueError(f"Base template '{base_template}' not found")
        
        # Create new template with modifications
        new_template = PromptTemplate(
            name=name,
            template=modifications.get("template", base.template),
            description=modifications.get("description", f"Variation of {base_template}"),
            parameters=modifications.get("parameters", base.parameters.copy()),
            few_shot_examples=modifications.get("few_shot_examples", base.few_shot_examples.copy()),
            version="1.0",
            tags=modifications.get("tags", base.tags.copy()),
        )
        
        self.save_template(new_template)
        return new_template
    
    def update_performance(
        self,
        template_name: str,
        metrics: Dict[str, float],
    ) -> None:
        """
        Update performance metrics for a template.
        
        Args:
            template_name: Template to update
            metrics: Performance metrics
        """
        template = self.get_template(template_name)
        if template:
            template.performance_metrics.update(metrics)
            self.save_template(template)