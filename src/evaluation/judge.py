"""LLM-based reasoning judge for evaluating explanation quality."""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.models import create_model
from src.core.types import ModelConfig
from src.core.exceptions import ModelAPIError


@dataclass
class JudgmentResult:
    """Result of judging a single reasoning explanation."""
    task_uid: str
    turn: Optional[int]  # For interactive tasks
    score: float  # 0.0 to 1.0 (scaled from 0-2 rubric)
    raw_score: int  # 0, 1, or 2
    feedback: str
    judge_model: str
    timestamp: datetime


class ReasoningJudge:
    """LLM-based judge for evaluating reasoning quality."""
    
    # Rubric definitions
    RUBRIC = {
        0: "Incorrect - reasoning contradicts board or conclusion",
        1: "Partial - partially correct logic but missing key inference",
        2: "Correct - clear, valid deduction fully supports answer"
    }
    
    def __init__(self, judge_model: Optional[ModelConfig] = None):
        """
        Initialize reasoning judge.
        
        Args:
            judge_model: Model config for judge (defaults to GPT-4)
        """
        if judge_model is None:
            judge_model = ModelConfig(
                name="openai/gpt-4o",
                provider="openai",
                model_id="gpt-4o",
                temperature=0.0,  # Deterministic judging
            )
        
        self.judge_model = create_model(judge_model)
        self.judge_model_name = judge_model.name
    
    async def judge_reasoning(
        self,
        task_uid: str,
        board_state: str,
        action: str,
        reasoning: str,
        ground_truth: Optional[str] = None,
        turn: Optional[int] = None,
    ) -> JudgmentResult:
        """
        Judge the quality of reasoning for a single move.
        
        Args:
            task_uid: Unique task identifier
            board_state: ASCII representation of board
            action: The action taken (e.g., "Reveal B3")
            reasoning: The model's reasoning explanation
            ground_truth: Optional correct answer for static tasks
            turn: Turn number for interactive tasks
        
        Returns:
            JudgmentResult with score and feedback
        """
        prompt = self._create_judge_prompt(
            board_state, action, reasoning, ground_truth
        )
        
        try:
            response = await self.judge_model.generate(prompt)
            raw_score, feedback = self._parse_judge_response(response.content)
            
            return JudgmentResult(
                task_uid=task_uid,
                turn=turn,
                score=raw_score / 2.0,  # Scale 0-2 to 0-1
                raw_score=raw_score,
                feedback=feedback,
                judge_model=self.judge_model_name,
                timestamp=datetime.utcnow(),
            )
            
        except Exception as e:
            # Default to partial score on error
            return JudgmentResult(
                task_uid=task_uid,
                turn=turn,
                score=0.5,
                raw_score=1,
                feedback=f"Judge error: {str(e)}",
                judge_model=self.judge_model_name,
                timestamp=datetime.utcnow(),
            )
    
    async def judge_episode(
        self,
        task_uid: str,
        episode_log: List[Dict[str, Any]],
    ) -> List[JudgmentResult]:
        """
        Judge all moves in an interactive episode.
        
        Args:
            task_uid: Unique task identifier
            episode_log: List of turns with board, action, reasoning
        
        Returns:
            List of judgment results for each turn
        """
        judgments = []
        
        for turn_data in episode_log:
            judgment = await self.judge_reasoning(
                task_uid=task_uid,
                board_state=turn_data["board"],
                action=turn_data["action"],
                reasoning=turn_data.get("rationale", ""),
                turn=turn_data["turn"],
            )
            judgments.append(judgment)
        
        return judgments
    
    def _create_judge_prompt(
        self,
        board_state: str,
        action: str,
        reasoning: str,
        ground_truth: Optional[str] = None,
    ) -> str:
        """Create prompt for judge model."""
        prompt = f"""You are evaluating the reasoning quality for a Minesweeper move.

Board State:
{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Action Taken: {action}

Model's Reasoning:
{reasoning}

"""
        
        if ground_truth:
            prompt += f"Correct Answer: {ground_truth}\n\n"
        
        prompt += f"""Evaluate the reasoning using this rubric:
- Score 0 (Incorrect): Reasoning contradicts the board state or reaches wrong conclusion
- Score 1 (Partial): Partially correct logic but missing key inferences or contains errors
- Score 2 (Correct): Clear, valid deduction that fully supports the answer

Provide your evaluation in this format:
SCORE: [0/1/2]
FEEDBACK: [Brief explanation of your score]

Focus on logical correctness, not writing style."""
        
        return prompt
    
    def _parse_judge_response(self, response: str) -> tuple[int, str]:
        """Parse score and feedback from judge response."""
        lines = response.strip().split('\n')
        
        score = 1  # Default to partial
        feedback = ""
        
        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    score = int(score_str[0])  # Get first digit
                    score = max(0, min(2, score))  # Clamp to 0-2
                except:
                    pass
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
        
        if not feedback:
            feedback = "No feedback provided"
        
        return score, feedback


class BatchJudge:
    """Batch processing for reasoning judgments."""
    
    def __init__(self, judge_model: Optional[ModelConfig] = None, parallel: int = 5):
        """
        Initialize batch judge.
        
        Args:
            judge_model: Model config for judge
            parallel: Number of parallel judgments
        """
        self.judge = ReasoningJudge(judge_model)
        self.parallel = parallel
    
    async def judge_batch(
        self,
        judgment_requests: List[Dict[str, Any]],
    ) -> List[JudgmentResult]:
        """
        Judge multiple reasoning samples in parallel.
        
        Args:
            judgment_requests: List of dicts with judgment parameters
        
        Returns:
            List of judgment results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(judgment_requests), self.parallel):
            batch = judgment_requests[i:i + self.parallel]
            
            tasks = [
                self.judge.judge_reasoning(**req)
                for req in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results