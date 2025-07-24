"""Prompt template system with assistance features for the competition platform."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import re
import json


class TemplateLevel(Enum):
    """Difficulty levels for prompt templates."""
    BEGINNER = "beginner"  # Mad Libs style with heavy guidance
    INTERMEDIATE = "intermediate"  # Structured with some flexibility
    ADVANCED = "advanced"  # Minimal structure, maximum flexibility
    EXPERT = "expert"  # No template, just hints


class TemplateCategory(Enum):
    """Categories of prompt templates."""
    GENERAL = "general"  # Works for most games
    STRATEGY = "strategy"  # Strategic reasoning focused
    SPEED = "speed"  # Optimized for quick completion
    CREATIVE = "creative"  # Encourages unique approaches
    EDUCATIONAL = "educational"  # Teaching-focused with explanations


@dataclass
class TemplateVariable:
    """A variable/placeholder in a template."""
    name: str
    description: str
    example: str
    required: bool = True
    validator: Optional[Callable[[str], bool]] = None
    autocomplete_options: List[str] = field(default_factory=list)
    max_length: Optional[int] = None
    
    def validate(self, value: str) -> bool:
        """Validate a value for this variable."""
        if self.required and not value:
            return False
        if self.max_length and len(value) > self.max_length:
            return False
        if self.validator:
            return self.validator(value)
        return True


@dataclass
class PromptTemplate:
    """A reusable prompt template."""
    template_id: str
    name: str
    description: str
    game_names: List[str]  # Games this template works for
    level: TemplateLevel
    category: TemplateCategory
    template_text: str
    variables: List[TemplateVariable]
    example_filled: str  # Example of filled template
    success_rate: float = 0.0  # Historical success rate
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def fill(self, values: Dict[str, str]) -> str:
        """Fill the template with provided values."""
        filled = self.template_text
        
        for variable in self.variables:
            placeholder = f"{{{variable.name}}}"
            value = values.get(variable.name, "")
            
            if variable.required and not value:
                raise ValueError(f"Required variable '{variable.name}' not provided")
            
            if not variable.validate(value):
                raise ValueError(f"Invalid value for variable '{variable.name}'")
            
            filled = filled.replace(placeholder, value)
        
        return filled
    
    def get_unfilled_variables(self, partial_values: Dict[str, str]) -> List[TemplateVariable]:
        """Get list of variables that still need values."""
        return [
            var for var in self.variables
            if var.name not in partial_values or not partial_values[var.name]
        ]


class PromptAssistant:
    """Intelligent prompt writing assistant."""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.snippets: Dict[str, List[str]] = self._load_snippets()
        self.common_patterns: Dict[str, str] = self._load_patterns()
        
    def _load_snippets(self) -> Dict[str, List[str]]:
        """Load common prompt snippets by category."""
        return {
            "opening": [
                "First, analyze the current state carefully.",
                "Let me think step by step.",
                "I'll approach this systematically.",
                "Starting with the most certain information,",
            ],
            "reasoning": [
                "Based on the constraints, I can deduce that",
                "The logical next step would be to",
                "Considering all possibilities,",
                "This pattern suggests that",
            ],
            "safety": [
                "I should avoid risky moves unless certain.",
                "It's better to gather more information first.",
                "I'll prioritize safe moves over speculation.",
                "Let me verify this is safe before proceeding.",
            ],
            "efficiency": [
                "To minimize moves, I should",
                "The most efficient approach would be",
                "I can save steps by",
                "Combining these insights allows me to",
            ],
            "closing": [
                "Therefore, my next move will be",
                "In conclusion, the best action is",
                "Based on this analysis, I'll",
                "My decision is to",
            ]
        }
    
    def _load_patterns(self) -> Dict[str, str]:
        """Load common successful prompt patterns."""
        return {
            "chain_of_thought": "Let me think through this step-by-step:\n1. {step1}\n2. {step2}\n3. {conclusion}",
            "pros_cons": "Considering {action}:\nPros: {pros}\nCons: {cons}\nDecision: {decision}",
            "if_then": "If {condition}, then {action}. Otherwise, {alternative}.",
            "priority_list": "My priorities in order:\n1. {priority1}\n2. {priority2}\n3. {priority3}",
            "constraint_check": "Given constraints:\n- {constraint1}\n- {constraint2}\nTherefore: {conclusion}",
        }
    
    def register_template(self, template: PromptTemplate):
        """Register a new template."""
        self.templates[template.template_id] = template
    
    def get_templates_for_game(
        self,
        game_name: str,
        level: Optional[TemplateLevel] = None,
        category: Optional[TemplateCategory] = None
    ) -> List[PromptTemplate]:
        """Get templates suitable for a specific game."""
        templates = []
        
        for template in self.templates.values():
            if game_name in template.game_names or "all" in template.game_names:
                if level and template.level != level:
                    continue
                if category and template.category != category:
                    continue
                templates.append(template)
        
        # Sort by success rate and usage
        templates.sort(key=lambda t: (t.success_rate, t.usage_count), reverse=True)
        return templates
    
    def suggest_completion(
        self,
        partial_prompt: str,
        game_context: Dict[str, Any],
        cursor_position: int
    ) -> List[Dict[str, Any]]:
        """Suggest completions based on partial prompt and context."""
        suggestions = []
        
        # Detect what type of content the user is writing
        lines = partial_prompt[:cursor_position].split('\n')
        current_line = lines[-1] if lines else ""
        
        # Check for snippet triggers
        for snippet_type, snippets in self.snippets.items():
            if self._should_suggest_snippet(current_line, snippet_type):
                for snippet in snippets[:3]:  # Top 3 suggestions
                    suggestions.append({
                        "type": "snippet",
                        "text": snippet,
                        "category": snippet_type,
                        "description": f"{snippet_type.title()} phrase"
                    })
        
        # Check for pattern completions
        for pattern_name, pattern in self.common_patterns.items():
            if self._matches_pattern_start(current_line, pattern):
                suggestions.append({
                    "type": "pattern",
                    "text": pattern,
                    "category": pattern_name,
                    "description": f"Complete {pattern_name.replace('_', ' ')} pattern"
                })
        
        # Game-specific suggestions
        game_suggestions = self._get_game_specific_suggestions(
            game_context.get("game_name", ""),
            current_line
        )
        suggestions.extend(game_suggestions)
        
        return suggestions[:6]  # Limit to 6 suggestions
    
    def _should_suggest_snippet(self, current_line: str, snippet_type: str) -> bool:
        """Determine if a snippet type should be suggested."""
        line_lower = current_line.lower().strip()
        
        triggers = {
            "opening": ["", "first", "start", "begin"],
            "reasoning": ["because", "since", "therefore", "thus"],
            "safety": ["safe", "risk", "careful", "avoid"],
            "efficiency": ["efficient", "quick", "fast", "optimal"],
            "closing": ["so", "thus", "therefore", "conclude"]
        }
        
        return any(trigger in line_lower for trigger in triggers.get(snippet_type, []))
    
    def _matches_pattern_start(self, current_line: str, pattern: str) -> bool:
        """Check if current line matches the start of a pattern."""
        # Simple check - could be more sophisticated
        pattern_start = pattern.split('{')[0].strip()
        return current_line.strip().startswith(pattern_start[:10])
    
    def _get_game_specific_suggestions(
        self,
        game_name: str,
        current_line: str
    ) -> List[Dict[str, Any]]:
        """Get game-specific suggestions."""
        suggestions = []
        
        if game_name == "minesweeper":
            if "reveal" in current_line.lower():
                suggestions.append({
                    "type": "game_action",
                    "text": "reveal the cell at row {row}, column {col}",
                    "category": "minesweeper",
                    "description": "Reveal action format"
                })
            elif "flag" in current_line.lower():
                suggestions.append({
                    "type": "game_action",
                    "text": "flag the cell at row {row}, column {col} as a mine",
                    "category": "minesweeper",
                    "description": "Flag action format"
                })
        
        elif game_name == "number_puzzle":
            if "guess" in current_line.lower() or "try" in current_line.lower():
                suggestions.append({
                    "type": "game_action",
                    "text": "guess {number} based on binary search strategy",
                    "category": "number_puzzle",
                    "description": "Guess format with strategy"
                })
        
        return suggestions
    
    def analyze_prompt_quality(self, prompt: str, game_name: str) -> Dict[str, Any]:
        """Analyze the quality of a written prompt."""
        analysis = {
            "length": len(prompt),
            "structure_score": 0.0,
            "clarity_score": 0.0,
            "strategy_score": 0.0,
            "suggestions": []
        }
        
        # Check length
        if analysis["length"] < 50:
            analysis["suggestions"].append("Consider adding more detail to your reasoning")
        elif analysis["length"] > 500:
            analysis["suggestions"].append("Try to be more concise")
        
        # Check structure (paragraphs, lists, etc.)
        lines = prompt.strip().split('\n')
        if len(lines) > 1:
            analysis["structure_score"] += 0.3
        if any(line.strip().startswith(('1.', '2.', '-', '*')) for line in lines):
            analysis["structure_score"] += 0.4
        if prompt.count('\n\n') > 0:  # Paragraphs
            analysis["structure_score"] += 0.3
        
        # Check clarity (simple heuristics)
        sentences = re.split(r'[.!?]+', prompt)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if 10 <= avg_sentence_length <= 20:
            analysis["clarity_score"] = 0.8
        elif 5 <= avg_sentence_length <= 30:
            analysis["clarity_score"] = 0.5
        else:
            analysis["clarity_score"] = 0.3
            analysis["suggestions"].append("Aim for clearer, medium-length sentences")
        
        # Check for strategy keywords
        strategy_keywords = [
            "strategy", "approach", "method", "plan", "because", "therefore",
            "first", "then", "finally", "if", "else", "consider"
        ]
        keyword_count = sum(1 for keyword in strategy_keywords if keyword in prompt.lower())
        analysis["strategy_score"] = min(1.0, keyword_count / 5)
        
        if analysis["strategy_score"] < 0.5:
            analysis["suggestions"].append("Include more strategic reasoning")
        
        # Overall score
        analysis["overall_score"] = (
            analysis["structure_score"] * 0.3 +
            analysis["clarity_score"] * 0.3 +
            analysis["strategy_score"] * 0.4
        )
        
        return analysis
    
    def generate_practice_prompt(
        self,
        game_name: str,
        difficulty: str = "beginner"
    ) -> Dict[str, Any]:
        """Generate a practice prompt for learning."""
        # Get appropriate template
        templates = self.get_templates_for_game(game_name, TemplateLevel.BEGINNER)
        
        if not templates:
            # Fallback to generic template
            template_text = """
I need to {action} in this {game_name} game.

First, I'll observe that {observation}.

My strategy is to {strategy}.

Therefore, my next move is to {specific_action}.
"""
            variables = [
                TemplateVariable("action", "What you want to accomplish", "find safe cells"),
                TemplateVariable("game_name", "The game being played", game_name),
                TemplateVariable("observation", "What you see on the board", "there are 3 flags placed"),
                TemplateVariable("strategy", "Your approach", "use process of elimination"),
                TemplateVariable("specific_action", "Exact move to make", "reveal cell at (2, 3)")
            ]
            
            template = PromptTemplate(
                template_id="generic_practice",
                name="Generic Practice Template",
                description="A simple template for practicing prompt writing",
                game_names=[game_name],
                level=TemplateLevel.BEGINNER,
                category=TemplateCategory.EDUCATIONAL,
                template_text=template_text,
                variables=variables,
                example_filled="[Example would go here]"
            )
        else:
            template = templates[0]
        
        return {
            "template": template,
            "instructions": self._get_practice_instructions(difficulty),
            "hints": self._get_practice_hints(game_name, difficulty)
        }
    
    def _get_practice_instructions(self, difficulty: str) -> List[str]:
        """Get practice instructions based on difficulty."""
        instructions = {
            "beginner": [
                "Fill in each blank with a relevant phrase",
                "Keep your responses simple and clear",
                "Focus on one action at a time"
            ],
            "intermediate": [
                "Expand on the template with your own reasoning",
                "Add specific details about your strategy",
                "Include if-then logic where appropriate"
            ],
            "advanced": [
                "Use the template as a starting point only",
                "Develop a comprehensive strategy",
                "Include contingency plans"
            ]
        }
        return instructions.get(difficulty, instructions["beginner"])
    
    def _get_practice_hints(self, game_name: str, difficulty: str) -> List[str]:
        """Get practice hints for specific games."""
        hints = {
            "minesweeper": [
                "Start with cells that have the most information",
                "Look for patterns in number arrangements",
                "Use flags to mark confirmed mines"
            ],
            "number_puzzle": [
                "Binary search cuts the search space in half",
                "Track the bounds after each guess",
                "Explain why you chose each number"
            ]
        }
        return hints.get(game_name, ["Think step by step", "Explain your reasoning"])


# Pre-built templates for immediate use
def create_default_templates() -> List[PromptTemplate]:
    """Create default templates for the system."""
    return [
        PromptTemplate(
            template_id="minesweeper_beginner",
            name="Minesweeper Starter",
            description="Simple template for Minesweeper moves",
            game_names=["minesweeper"],
            level=TemplateLevel.BEGINNER,
            category=TemplateCategory.GENERAL,
            template_text="""I need to make a move in Minesweeper.

Looking at the board, I can see {observation}.

Based on this, {reasoning}.

My move: {action} at position ({row}, {col}).""",
            variables=[
                TemplateVariable("observation", "What you see on the board", "a '2' next to two hidden cells"),
                TemplateVariable("reasoning", "Your logical deduction", "both cells must be mines"),
                TemplateVariable("action", "reveal or flag", "flag"),
                TemplateVariable("row", "Row number", "3"),
                TemplateVariable("col", "Column number", "5")
            ],
            example_filled="""I need to make a move in Minesweeper.

Looking at the board, I can see a '2' next to two hidden cells.

Based on this, both cells must be mines.

My move: flag at position (3, 5)."""
        ),
        
        PromptTemplate(
            template_id="strategy_advanced",
            name="Strategic Reasoning",
            description="Advanced template focusing on strategy",
            game_names=["all"],
            level=TemplateLevel.ADVANCED,
            category=TemplateCategory.STRATEGY,
            template_text="""Strategic Analysis:

Current State: {state_summary}

Objectives in priority order:
1. {primary_objective}
2. {secondary_objective}

Constraints to consider:
- {constraint_1}
- {constraint_2}

Evaluating options:
{option_analysis}

Decision: {final_decision}

Reasoning: {detailed_reasoning}""",
            variables=[
                TemplateVariable("state_summary", "Summary of current game state", "Board is 40% revealed with 5 mines identified"),
                TemplateVariable("primary_objective", "Most important goal", "Identify remaining mines safely"),
                TemplateVariable("secondary_objective", "Secondary goal", "Maximize information gain"),
                TemplateVariable("constraint_1", "First constraint", "Limited safe moves available"),
                TemplateVariable("constraint_2", "Second constraint", "Time pressure"),
                TemplateVariable("option_analysis", "Analysis of possible moves", "Option A gives 80% certainty..."),
                TemplateVariable("final_decision", "Your chosen action", "Reveal cell at (4, 7)"),
                TemplateVariable("detailed_reasoning", "Why this is best", "This move guarantees safety and opens up the most cells")
            ],
            example_filled="[Full example would be provided]"
        )
    ]