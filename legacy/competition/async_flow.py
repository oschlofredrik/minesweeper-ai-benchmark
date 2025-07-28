"""Asynchronous game flow management for handling AI evaluation delays."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from collections import defaultdict

from src.evaluation.generic_engine import GenericEvaluationEngine, GameEvaluationResult


class PlayerStatus(Enum):
    """Status of a player in the current round."""
    WAITING = "waiting"  # Waiting to start
    WRITING = "writing"  # Writing their prompt
    SUBMITTED = "submitted"  # Prompt submitted, waiting for evaluation
    EVALUATING = "evaluating"  # AI is evaluating their prompt
    COMPLETED = "completed"  # Evaluation complete
    VIEWING = "viewing"  # Viewing results while others finish
    ERROR = "error"  # Error occurred during evaluation


class FlowMode(Enum):
    """Different flow modes for handling asynchronous gameplay."""
    SYNCHRONOUS = "synchronous"  # Everyone waits for all to complete (Kahoot-style)
    STAGGERED = "staggered"  # Players can start when ready
    CONTINUOUS = "continuous"  # Move to next round immediately after completion
    PACED = "paced"  # Timed checkpoints where groups advance together


@dataclass
class PlayerRoundState:
    """State of a player in a specific round."""
    player_id: str
    round_number: int
    status: PlayerStatus = PlayerStatus.WAITING
    prompt: Optional[str] = None
    submitted_at: Optional[datetime] = None
    evaluation_started_at: Optional[datetime] = None
    evaluation_completed_at: Optional[datetime] = None
    result: Optional[GameEvaluationResult] = None
    error_message: Optional[str] = None
    engagement_score: float = 0.0  # Track engagement during wait times
    
    @property
    def time_writing(self) -> Optional[timedelta]:
        """Time spent writing the prompt."""
        if self.submitted_at and self.status != PlayerStatus.WAITING:
            return self.submitted_at - (self.evaluation_started_at or datetime.utcnow())
        return None
    
    @property
    def time_evaluating(self) -> Optional[timedelta]:
        """Time spent in AI evaluation."""
        if self.evaluation_started_at:
            end_time = self.evaluation_completed_at or datetime.utcnow()
            return end_time - self.evaluation_started_at
        return None


@dataclass
class WaitingActivity:
    """Activity for players while waiting for others."""
    activity_id: str
    name: str
    description: str
    activity_type: str  # "mini_game", "tutorial", "review", "predict", "social"
    duration_estimate: int  # seconds
    engagement_points: float  # Points for participating
    content: Dict[str, Any]  # Activity-specific content


class AsyncGameFlowManager:
    """Manages asynchronous game flow with engagement during wait times."""
    
    def __init__(
        self,
        evaluation_engine: GenericEvaluationEngine,
        flow_mode: FlowMode = FlowMode.SYNCHRONOUS
    ):
        self.evaluation_engine = evaluation_engine
        self.flow_mode = flow_mode
        self.player_states: Dict[str, Dict[int, PlayerRoundState]] = defaultdict(dict)
        self.round_timers: Dict[int, datetime] = {}
        self.waiting_activities: List[WaitingActivity] = self._initialize_activities()
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.evaluation_queue: asyncio.Queue = asyncio.Queue()
        self.active_evaluations: Dict[str, asyncio.Task] = {}
    
    def _initialize_activities(self) -> List[WaitingActivity]:
        """Initialize waiting activities for players."""
        return [
            WaitingActivity(
                activity_id="watch_replay",
                name="Watch Your AI Play",
                description="See how the AI executes your prompt",
                activity_type="review",
                duration_estimate=30,
                engagement_points=10.0,
                content={"auto_play": True, "speed": 2.0}
            ),
            WaitingActivity(
                activity_id="predict_scores",
                name="Predict Other Scores",
                description="Guess how well others will do",
                activity_type="predict",
                duration_estimate=20,
                engagement_points=15.0,
                content={"show_hints": True}
            ),
            WaitingActivity(
                activity_id="strategy_tips",
                name="Strategy Guide",
                description="Learn advanced strategies for this game",
                activity_type="tutorial",
                duration_estimate=45,
                engagement_points=20.0,
                content={"difficulty": "adaptive"}
            ),
            WaitingActivity(
                activity_id="prompt_puzzle",
                name="Prompt Puzzle",
                description="Solve a mini prompt challenge",
                activity_type="mini_game",
                duration_estimate=60,
                engagement_points=25.0,
                content={"puzzle_type": "fill_in_blank"}
            )
        ]
    
    def register_callback(self, event: str, callback: Callable):
        """Register a callback for specific events."""
        self.event_callbacks[event].append(callback)
    
    async def _emit_event(self, event: str, data: Any):
        """Emit an event to all registered callbacks."""
        for callback in self.event_callbacks[event]:
            await callback(data)
    
    async def start_round(
        self,
        round_number: int,
        players: List[str],
        time_limit: Optional[int] = None
    ):
        """Start a new round for all players."""
        self.round_timers[round_number] = datetime.utcnow()
        
        # Initialize player states
        for player_id in players:
            self.player_states[player_id][round_number] = PlayerRoundState(
                player_id=player_id,
                round_number=round_number,
                status=PlayerStatus.WRITING
            )
        
        await self._emit_event("round_started", {
            "round": round_number,
            "players": players,
            "time_limit": time_limit,
            "flow_mode": self.flow_mode.value
        })
        
        # Start evaluation worker if not running
        if not hasattr(self, '_evaluation_worker'):
            self._evaluation_worker = asyncio.create_task(self._process_evaluation_queue())
    
    async def submit_prompt(
        self,
        player_id: str,
        round_number: int,
        prompt: str,
        game_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit a player's prompt for evaluation."""
        state = self.player_states[player_id].get(round_number)
        if not state:
            return {"error": "Player not in this round"}
        
        if state.status != PlayerStatus.WRITING:
            return {"error": f"Cannot submit in status {state.status.value}"}
        
        # Update state
        state.prompt = prompt
        state.submitted_at = datetime.utcnow()
        state.status = PlayerStatus.SUBMITTED
        
        # Add to evaluation queue
        await self.evaluation_queue.put({
            "player_id": player_id,
            "round_number": round_number,
            "prompt": prompt,
            "game_config": game_config,
            "submitted_at": state.submitted_at
        })
        
        await self._emit_event("prompt_submitted", {
            "player_id": player_id,
            "round": round_number,
            "queue_size": self.evaluation_queue.qsize()
        })
        
        # Return waiting activities based on flow mode
        if self.flow_mode == FlowMode.SYNCHRONOUS:
            activities = self._get_waiting_activities(player_id, round_number)
            return {
                "status": "submitted",
                "message": "Prompt submitted successfully",
                "waiting_activities": activities,
                "estimated_wait": self._estimate_wait_time()
            }
        else:
            return {
                "status": "submitted",
                "message": "Prompt submitted successfully",
                "next_action": "watch_evaluation"
            }
    
    async def _process_evaluation_queue(self):
        """Process prompts from the evaluation queue."""
        while True:
            try:
                # Get next prompt to evaluate
                eval_request = await self.evaluation_queue.get()
                
                player_id = eval_request["player_id"]
                round_number = eval_request["round_number"]
                state = self.player_states[player_id][round_number]
                
                # Update status
                state.status = PlayerStatus.EVALUATING
                state.evaluation_started_at = datetime.utcnow()
                
                await self._emit_event("evaluation_started", {
                    "player_id": player_id,
                    "round": round_number
                })
                
                # Create evaluation task
                eval_task = asyncio.create_task(
                    self._evaluate_prompt(eval_request)
                )
                self.active_evaluations[f"{player_id}_{round_number}"] = eval_task
                
                # Don't wait for completion in queue processor
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in evaluation queue: {e}")
    
    async def _evaluate_prompt(self, eval_request: Dict[str, Any]):
        """Evaluate a single prompt."""
        player_id = eval_request["player_id"]
        round_number = eval_request["round_number"]
        state = self.player_states[player_id][round_number]
        
        try:
            # This would call the actual evaluation engine
            # For now, simulate with a delay
            await asyncio.sleep(5)  # Simulate AI evaluation time
            
            # In real implementation:
            # result = await self.evaluation_engine.evaluate_game(...)
            
            state.status = PlayerStatus.COMPLETED
            state.evaluation_completed_at = datetime.utcnow()
            # state.result = result
            
            await self._emit_event("evaluation_completed", {
                "player_id": player_id,
                "round": round_number,
                "success": True
            })
            
            # Check if round is complete
            await self._check_round_completion(round_number)
            
        except Exception as e:
            state.status = PlayerStatus.ERROR
            state.error_message = str(e)
            
            await self._emit_event("evaluation_error", {
                "player_id": player_id,
                "round": round_number,
                "error": str(e)
            })
        
        finally:
            # Remove from active evaluations
            task_key = f"{player_id}_{round_number}"
            if task_key in self.active_evaluations:
                del self.active_evaluations[task_key]
    
    def _get_waiting_activities(
        self,
        player_id: str,
        round_number: int
    ) -> List[Dict[str, Any]]:
        """Get appropriate waiting activities for a player."""
        state = self.player_states[player_id][round_number]
        
        # Filter activities based on estimated wait time
        wait_time = self._estimate_wait_time()
        suitable_activities = [
            {
                "id": activity.activity_id,
                "name": activity.name,
                "description": activity.description,
                "type": activity.activity_type,
                "duration": activity.duration_estimate,
                "points": activity.engagement_points,
                "available": activity.duration_estimate <= wait_time
            }
            for activity in self.waiting_activities
        ]
        
        return sorted(suitable_activities, key=lambda x: x["points"], reverse=True)
    
    def _estimate_wait_time(self) -> int:
        """Estimate wait time based on queue and evaluation times."""
        # Simple estimation - would be more sophisticated in practice
        queue_size = self.evaluation_queue.qsize()
        avg_eval_time = 10  # seconds, would track actual averages
        
        # Estimate based on queue position and parallel processing
        parallel_workers = 3  # Number of concurrent evaluations
        estimated_wait = (queue_size / parallel_workers) * avg_eval_time
        
        return int(estimated_wait)
    
    async def _check_round_completion(self, round_number: int):
        """Check if all players have completed the round."""
        round_states = [
            states[round_number]
            for states in self.player_states.values()
            if round_number in states
        ]
        
        all_complete = all(
            state.status in [PlayerStatus.COMPLETED, PlayerStatus.ERROR]
            for state in round_states
        )
        
        if all_complete:
            await self._emit_event("round_completed", {
                "round": round_number,
                "completion_time": datetime.utcnow()
            })
            
            # Handle flow mode specific actions
            if self.flow_mode == FlowMode.SYNCHRONOUS:
                await self._show_round_results(round_number)
            elif self.flow_mode == FlowMode.CONTINUOUS:
                await self._auto_advance_players(round_number)
    
    async def _show_round_results(self, round_number: int):
        """Show results to all players simultaneously."""
        results = []
        
        for player_states in self.player_states.values():
            if round_number in player_states:
                state = player_states[round_number]
                results.append({
                    "player_id": state.player_id,
                    "status": state.status.value,
                    "time_writing": state.time_writing.total_seconds() if state.time_writing else None,
                    "time_evaluating": state.time_evaluating.total_seconds() if state.time_evaluating else None,
                    "engagement_score": state.engagement_score,
                    "result": state.result.to_dict() if state.result else None
                })
        
        await self._emit_event("show_results", {
            "round": round_number,
            "results": results
        })
    
    async def _auto_advance_players(self, round_number: int):
        """Automatically advance players who completed to next round."""
        for player_states in self.player_states.values():
            if round_number in player_states:
                state = player_states[round_number]
                if state.status == PlayerStatus.COMPLETED:
                    await self._emit_event("player_advance", {
                        "player_id": state.player_id,
                        "from_round": round_number,
                        "to_round": round_number + 1
                    })
    
    async def record_engagement(
        self,
        player_id: str,
        round_number: int,
        activity_id: str,
        engagement_data: Dict[str, Any]
    ):
        """Record player engagement during wait time."""
        state = self.player_states[player_id].get(round_number)
        if not state:
            return
        
        # Find activity
        activity = next(
            (a for a in self.waiting_activities if a.activity_id == activity_id),
            None
        )
        
        if activity:
            # Award engagement points
            points = activity.engagement_points * engagement_data.get("completion", 1.0)
            state.engagement_score += points
            
            await self._emit_event("engagement_recorded", {
                "player_id": player_id,
                "round": round_number,
                "activity": activity_id,
                "points": points
            })
    
    def get_round_status(self, round_number: int) -> Dict[str, Any]:
        """Get current status of a round."""
        round_states = [
            states[round_number]
            for states in self.player_states.values()
            if round_number in states
        ]
        
        status_counts = defaultdict(int)
        for state in round_states:
            status_counts[state.status.value] += 1
        
        return {
            "round": round_number,
            "total_players": len(round_states),
            "status_breakdown": dict(status_counts),
            "queue_size": self.evaluation_queue.qsize(),
            "active_evaluations": len(self.active_evaluations),
            "estimated_completion": self._estimate_round_completion(round_number)
        }
    
    def _estimate_round_completion(self, round_number: int) -> Optional[datetime]:
        """Estimate when the round will complete."""
        pending_count = sum(
            1 for states in self.player_states.values()
            if round_number in states and states[round_number].status not in [
                PlayerStatus.COMPLETED, PlayerStatus.ERROR
            ]
        )
        
        if pending_count == 0:
            return datetime.utcnow()
        
        # Estimate based on evaluation rate
        avg_eval_time = 10  # seconds
        completion_time = datetime.utcnow() + timedelta(
            seconds=pending_count * avg_eval_time / 3  # parallel processing
        )
        
        return completion_time