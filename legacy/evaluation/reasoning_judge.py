"""LLM-based judge for evaluating reasoning quality."""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import json

from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.openai import OpenAIModel

logger = get_logger("evaluation.reasoning_judge")


@dataclass
class ReasoningJudgment:
    """Result of judging reasoning quality."""
    task_uid: str
    raw_score: int  # 0, 1, or 2
    normalized_score: float  # 0.0 to 1.0
    feedback: str
    confidence: str  # "high", "medium", "low"
    timestamp: datetime


class ReasoningJudge:
    """Evaluates reasoning quality using an LLM judge."""
    
    def __init__(self, judge_model: str = "gpt-4o", temperature: float = 0.0):
        """
        Initialize reasoning judge.
        
        Args:
            judge_model: Model to use for judging (default: gpt-4o)
            temperature: Temperature for judge model (default: 0 for deterministic)
        """
        self.judge_model_name = judge_model
        self.temperature = temperature
        
        # Initialize judge model
        self.judge = OpenAIModel({
            "model_id": judge_model,
            "temperature": temperature,
            "max_tokens": 500,
            "api_key": settings.openai_api_key
        })
        
        logger.info(f"Initialized reasoning judge with model: {judge_model}")
    
    def _create_judge_prompt(
        self,
        task_type: str,
        board_state: str,
        action: str,
        reasoning: str,
        correct_action: Optional[str] = None
    ) -> str:
        """Create prompt for the judge model."""
        prompt = f"""You are an expert judge evaluating reasoning quality in Minesweeper.

Task Type: {task_type}
Board State:
{board_state}

Player's Action: {action}
Player's Reasoning: {reasoning}
"""
        
        if correct_action and task_type == "static":
            prompt += f"\nCorrect Action: {correct_action}\n"
        
        prompt += """
Evaluate the reasoning using this rubric:

Score 0 (Incorrect):
- Reasoning contradicts the board state
- Logic is fundamentally flawed
- Conclusion doesn't follow from premises
- Misinterprets game rules

Score 1 (Partial):
- Some correct observations but incomplete analysis
- Minor logical errors that don't invalidate conclusion
- Correct conclusion but weak justification
- Missing some important deductions

Score 2 (Correct):
- Clear, valid logical deduction
- Considers all relevant information
- Reasoning fully supports the action
- No logical errors

Provide your evaluation in JSON format:
{
    "score": <0, 1, or 2>,
    "confidence": "<high, medium, or low>",
    "feedback": "<brief explanation of score>"
}

Focus on the logical validity of the reasoning, not just whether the action is correct."""
        
        return prompt
    
    async def judge_reasoning(
        self,
        task_uid: str,
        board_state: str,
        action: str,
        reasoning: str,
        task_type: str = "interactive",
        correct_action: Optional[str] = None
    ) -> ReasoningJudgment:
        """
        Judge the quality of reasoning for a single move/prediction.
        
        Args:
            task_uid: Unique task identifier
            board_state: ASCII representation of board
            action: The action taken/predicted
            reasoning: The reasoning provided
            task_type: "static" or "interactive"
            correct_action: Correct action (for static tasks)
        
        Returns:
            ReasoningJudgment object
        """
        # Create judge prompt
        prompt = self._create_judge_prompt(
            task_type, board_state, action, reasoning, correct_action
        )
        
        try:
            # Get judgment from model
            response = await self.judge.generate(prompt, use_functions=False)
            
            # Parse JSON response
            content = response.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Parse JSON
            try:
                judgment_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON object
                import re
                json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
                if json_match:
                    judgment_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse judge response as JSON")
            
            # Extract fields
            raw_score = judgment_data.get("score", 0)
            confidence = judgment_data.get("confidence", "medium")
            feedback = judgment_data.get("feedback", "No feedback provided")
            
            # Validate score
            if raw_score not in [0, 1, 2]:
                logger.warning(f"Invalid score {raw_score}, defaulting to 0")
                raw_score = 0
            
            # Normalize score to 0-1
            normalized_score = raw_score / 2.0
            
            return ReasoningJudgment(
                task_uid=task_uid,
                raw_score=raw_score,
                normalized_score=normalized_score,
                feedback=feedback,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error judging reasoning: {e}", exc_info=True)
            
            # Return default low score on error
            return ReasoningJudgment(
                task_uid=task_uid,
                raw_score=0,
                normalized_score=0.0,
                feedback=f"Judge error: {str(e)}",
                confidence="low",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def judge_transcript(
        self,
        transcript: Any,  # GameTranscript
        task_type: str = "interactive"
    ) -> List[ReasoningJudgment]:
        """
        Judge all moves in a game transcript.
        
        Args:
            transcript: Game transcript with moves
            task_type: Type of task
        
        Returns:
            List of judgments for each move
        """
        judgments = []
        
        for i, move in enumerate(transcript.moves):
            if not move.model_reasoning:
                # Skip moves without reasoning
                continue
            
            # Get board state before the move
            board_state = move.board_state_before
            
            # Create task UID for this move
            move_uid = f"{transcript.task_id}-move{i+1}"
            
            # Judge the reasoning
            judgment = await self.judge_reasoning(
                task_uid=move_uid,
                board_state=board_state,
                action=move.action.to_string(),
                reasoning=move.model_reasoning,
                task_type=task_type
            )
            
            judgments.append(judgment)
        
        return judgments
    
    
    def calculate_aggregate_score(
        self,
        judgments: List[ReasoningJudgment],
        weighting: str = "uniform"
    ) -> float:
        """
        Calculate aggregate reasoning score.
        
        Args:
            judgments: List of individual judgments
            weighting: How to weight scores ("uniform" or "confidence")
        
        Returns:
            Aggregate score (0.0 to 1.0)
        """
        if not judgments:
            return 0.0
        
        if weighting == "uniform":
            # Simple average
            return sum(j.normalized_score for j in judgments) / len(judgments)
        
        elif weighting == "confidence":
            # Weight by confidence
            confidence_weights = {
                "high": 1.0,
                "medium": 0.8,
                "low": 0.5
            }
            
            total_weight = sum(
                confidence_weights.get(j.confidence, 0.5) 
                for j in judgments
            )
            
            if total_weight == 0:
                return 0.0
            
            weighted_sum = sum(
                j.normalized_score * confidence_weights.get(j.confidence, 0.5)
                for j in judgments
            )
            
            return weighted_sum / total_weight
        
        else:
            raise ValueError(f"Unknown weighting method: {weighting}")
    


