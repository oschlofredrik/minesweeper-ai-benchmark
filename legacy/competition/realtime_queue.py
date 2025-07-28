"""Real-time evaluation queue and progress tracking system."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from collections import defaultdict
import json


class QueuePriority(Enum):
    """Priority levels for queue items."""
    HIGH = 1  # Practice mode, premium users
    NORMAL = 2  # Regular competition
    LOW = 3  # Background tasks


class EvaluationStatus(Enum):
    """Status of an evaluation task."""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """An item in the evaluation queue."""
    item_id: str
    player_id: str
    session_id: str
    round_number: int
    game_name: str
    prompt: str
    priority: QueuePriority
    submitted_at: datetime
    status: EvaluationStatus = EvaluationStatus.QUEUED
    assigned_to: Optional[str] = None  # Worker ID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def wait_time(self) -> Optional[timedelta]:
        """Time spent waiting in queue."""
        if self.started_at:
            return self.started_at - self.submitted_at
        return datetime.utcnow() - self.submitted_at
    
    @property
    def processing_time(self) -> Optional[timedelta]:
        """Time spent processing."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return None
    
    @property
    def total_time(self) -> timedelta:
        """Total time from submission to completion."""
        end_time = self.completed_at or datetime.utcnow()
        return end_time - self.submitted_at


@dataclass
class WorkerStats:
    """Statistics for an evaluation worker."""
    worker_id: str
    status: str  # idle, busy, offline
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_processing_time: float = 0.0  # seconds
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    
    def update_heartbeat(self):
        """Update last heartbeat time."""
        self.last_heartbeat = datetime.utcnow()
    
    @property
    def is_healthy(self) -> bool:
        """Check if worker is healthy based on heartbeat."""
        return (datetime.utcnow() - self.last_heartbeat).seconds < 30


class RealTimeEvaluationQueue:
    """Manages real-time evaluation queue with progress tracking."""
    
    def __init__(self, max_workers: int = 5):
        self.queue: List[QueueItem] = []
        self.processing: Dict[str, QueueItem] = {}  # item_id -> QueueItem
        self.completed: Dict[str, QueueItem] = {}  # Limited history
        self.workers: Dict[str, WorkerStats] = {}
        self.max_workers = max_workers
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.queue_metrics = QueueMetrics()
        self._lock: Optional[asyncio.Lock] = None
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        self._maintenance_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Initialize async resources if not already done."""
        if not self._initialized:
            self._lock = asyncio.Lock()
            self._maintenance_task = asyncio.create_task(self._maintenance_loop())
            self._initialized = True
    
    async def submit(
        self,
        player_id: str,
        session_id: str,
        round_number: int,
        game_name: str,
        prompt: str,
        priority: QueuePriority = QueuePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Submit a new evaluation task to the queue."""
        await self._ensure_initialized()
        
        item = QueueItem(
            item_id=str(uuid.uuid4()),
            player_id=player_id,
            session_id=session_id,
            round_number=round_number,
            game_name=game_name,
            prompt=prompt,
            priority=priority,
            submitted_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        async with self._lock:
            # Insert based on priority
            insert_pos = 0
            for i, existing in enumerate(self.queue):
                if existing.priority.value > item.priority.value:
                    insert_pos = i
                    break
                insert_pos = i + 1
            
            self.queue.insert(insert_pos, item)
            self.queue_metrics.record_submission(item)
        
        # Notify subscribers
        await self._publish_update("item_queued", {
            "item_id": item.item_id,
            "player_id": player_id,
            "position": insert_pos + 1,
            "queue_length": len(self.queue)
        })
        
        # Try to assign to available worker
        await self._try_assign_tasks()
        
        return item.item_id
    
    async def cancel(self, item_id: str) -> bool:
        """Cancel a queued evaluation."""
        async with self._lock:
            # Check if in queue
            for i, item in enumerate(self.queue):
                if item.item_id == item_id:
                    item.status = EvaluationStatus.CANCELLED
                    self.queue.pop(i)
                    await self._publish_update("item_cancelled", {
                        "item_id": item_id
                    })
                    return True
            
            # Check if processing
            if item_id in self.processing:
                item = self.processing[item_id]
                item.status = EvaluationStatus.CANCELLED
                # Worker will handle cleanup
                return True
        
        return False
    
    async def register_worker(self, worker_id: str) -> bool:
        """Register a new evaluation worker."""
        if len(self.workers) >= self.max_workers:
            return False
        
        async with self._lock:
            self.workers[worker_id] = WorkerStats(
                worker_id=worker_id,
                status="idle"
            )
        
        # Start worker task
        self._worker_tasks[worker_id] = asyncio.create_task(
            self._worker_loop(worker_id)
        )
        
        await self._publish_update("worker_registered", {
            "worker_id": worker_id,
            "total_workers": len(self.workers)
        })
        
        return True
    
    async def _worker_loop(self, worker_id: str):
        """Main loop for a worker."""
        while worker_id in self.workers:
            try:
                # Update heartbeat
                self.workers[worker_id].update_heartbeat()
                
                # Try to get work
                item = await self._get_next_item(worker_id)
                if item:
                    await self._process_item(worker_id, item)
                else:
                    # No work available, wait
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)
    
    async def _get_next_item(self, worker_id: str) -> Optional[QueueItem]:
        """Get next item from queue for worker."""
        async with self._lock:
            if not self.queue:
                return None
            
            # Get highest priority item
            item = self.queue.pop(0)
            item.status = EvaluationStatus.ASSIGNED
            item.assigned_to = worker_id
            item.started_at = datetime.utcnow()
            
            # Move to processing
            self.processing[item.item_id] = item
            
            # Update worker status
            self.workers[worker_id].status = "busy"
            self.workers[worker_id].current_task = item.item_id
        
        await self._publish_update("item_assigned", {
            "item_id": item.item_id,
            "worker_id": worker_id,
            "wait_time": item.wait_time.total_seconds()
        })
        
        return item
    
    async def _process_item(self, worker_id: str, item: QueueItem):
        """Process an evaluation item."""
        try:
            # Update status
            item.status = EvaluationStatus.PROCESSING
            
            await self._publish_update("item_processing", {
                "item_id": item.item_id,
                "player_id": item.player_id,
                "game_name": item.game_name
            })
            
            # Simulate evaluation (in real implementation, call evaluation engine)
            await asyncio.sleep(5)  # Simulate processing time
            
            # Mock result
            result = {
                "score": 0.85,
                "moves": 12,
                "success": True,
                "details": "Evaluation completed successfully"
            }
            
            # Complete item
            async with self._lock:
                item.status = EvaluationStatus.COMPLETED
                item.completed_at = datetime.utcnow()
                item.result = result
                
                # Move to completed
                if item.item_id in self.processing:
                    del self.processing[item.item_id]
                self.completed[item.item_id] = item
                
                # Update worker stats
                worker = self.workers[worker_id]
                worker.status = "idle"
                worker.current_task = None
                worker.tasks_completed += 1
                
                # Update average processing time
                processing_time = item.processing_time.total_seconds()
                worker.average_processing_time = (
                    (worker.average_processing_time * (worker.tasks_completed - 1) + 
                     processing_time) / worker.tasks_completed
                )
            
            # Record metrics
            self.queue_metrics.record_completion(item)
            
            await self._publish_update("item_completed", {
                "item_id": item.item_id,
                "player_id": item.player_id,
                "result": result,
                "processing_time": processing_time,
                "total_time": item.total_time.total_seconds()
            })
            
        except Exception as e:
            # Handle failure
            async with self._lock:
                item.status = EvaluationStatus.FAILED
                item.error = str(e)
                item.retry_count += 1
                
                if item.retry_count < item.max_retries:
                    # Requeue for retry
                    item.status = EvaluationStatus.QUEUED
                    self.queue.append(item)
                    if item.item_id in self.processing:
                        del self.processing[item.item_id]
                else:
                    # Max retries reached
                    if item.item_id in self.processing:
                        del self.processing[item.item_id]
                    self.completed[item.item_id] = item
                
                # Update worker stats
                worker = self.workers[worker_id]
                worker.status = "idle"
                worker.current_task = None
                worker.tasks_failed += 1
            
            await self._publish_update("item_failed", {
                "item_id": item.item_id,
                "error": str(e),
                "retry_count": item.retry_count,
                "will_retry": item.retry_count < item.max_retries
            })
    
    async def _try_assign_tasks(self):
        """Try to assign queued tasks to available workers."""
        async with self._lock:
            available_workers = [
                w for w in self.workers.values()
                if w.status == "idle" and w.is_healthy
            ]
            
            # Assign tasks to available workers
            for worker in available_workers:
                if not self.queue:
                    break
                
                # Worker will pick up task in its loop
                pass
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        # Return basic status if not initialized
        if not self._initialized or self._lock is None:
            return {
                "queue_length": 0,
                "processing_count": 0,
                "workers": {"total": 0, "idle": 0, "busy": 0, "healthy": 0},
                "metrics": {},
                "estimated_wait_time": 0,
                "queue_by_priority": {}
            }
        
        # Can't use async lock in sync context, so return current snapshot
        # In production, use Redis or similar for thread-safe access
        status = {
            "queue_length": len(self.queue),
            "processing_count": len(self.processing),
            "workers": {
                "total": len(self.workers),
                "idle": sum(1 for w in self.workers.values() if w.status == "idle"),
                "busy": sum(1 for w in self.workers.values() if w.status == "busy"),
                "healthy": sum(1 for w in self.workers.values() if w.is_healthy)
            },
            "metrics": self.queue_metrics.get_summary(),
            "estimated_wait_time": self._estimate_wait_time()
        }
        
        # Add queue breakdown by priority
        priority_counts = defaultdict(int)
        for item in self.queue:
            priority_counts[item.priority.value] += 1
        status["queue_by_priority"] = dict(priority_counts)
        
        return status
    
    def get_position(self, item_id: str) -> Optional[int]:
        """Get queue position for an item."""
        for i, item in enumerate(self.queue):
            if item.item_id == item_id:
                return i + 1
        return None
    
    def get_item_status(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a specific item."""
        # Check queue
        for i, item in enumerate(self.queue):
            if item.item_id == item_id:
                return {
                    "status": item.status.value,
                    "position": i + 1,
                    "wait_time": item.wait_time.total_seconds(),
                    "estimated_processing_time": self._estimate_processing_time(item.game_name)
                }
        
        # Check processing
        if item_id in self.processing:
            item = self.processing[item_id]
            return {
                "status": item.status.value,
                "worker_id": item.assigned_to,
                "processing_time": item.processing_time.total_seconds() if item.processing_time else 0
            }
        
        # Check completed
        if item_id in self.completed:
            item = self.completed[item_id]
            return {
                "status": item.status.value,
                "result": item.result,
                "total_time": item.total_time.total_seconds(),
                "error": item.error
            }
        
        return None
    
    def _estimate_wait_time(self) -> float:
        """Estimate wait time for new submissions."""
        if not self.workers:
            return 0
        
        # Calculate based on queue size and worker capacity
        active_workers = sum(1 for w in self.workers.values() if w.is_healthy)
        if active_workers == 0:
            return float('inf')
        
        # Average processing time across all workers
        avg_processing_time = sum(
            w.average_processing_time for w in self.workers.values()
            if w.average_processing_time > 0
        ) / max(1, sum(1 for w in self.workers.values() if w.average_processing_time > 0))
        
        if avg_processing_time == 0:
            avg_processing_time = 10  # Default estimate
        
        # Simple estimation
        queue_depth = len(self.queue)
        estimated_wait = (queue_depth / active_workers) * avg_processing_time
        
        return estimated_wait
    
    def _estimate_processing_time(self, game_name: str) -> float:
        """Estimate processing time for a specific game."""
        # In real implementation, track per-game statistics
        return 10.0  # Default estimate
    
    def subscribe(self, event: str, callback: Callable):
        """Subscribe to queue events."""
        self.subscribers[event].add(callback)
    
    def unsubscribe(self, event: str, callback: Callable):
        """Unsubscribe from queue events."""
        self.subscribers[event].discard(callback)
    
    async def _publish_update(self, event: str, data: Dict[str, Any]):
        """Publish update to subscribers."""
        if event in self.subscribers:
            # Add timestamp
            data["timestamp"] = datetime.utcnow().isoformat()
            
            # Call all subscribers
            tasks = [
                callback(event, data)
                for callback in self.subscribers[event]
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks."""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Clean old completed items
                async with self._lock:
                    cutoff = datetime.utcnow() - timedelta(hours=1)
                    old_items = [
                        item_id for item_id, item in self.completed.items()
                        if item.completed_at and item.completed_at < cutoff
                    ]
                    for item_id in old_items:
                        del self.completed[item_id]
                
                # Check worker health
                unhealthy_workers = [
                    worker_id for worker_id, worker in self.workers.items()
                    if not worker.is_healthy
                ]
                for worker_id in unhealthy_workers:
                    await self._handle_unhealthy_worker(worker_id)
                
                # Update metrics
                self.queue_metrics.calculate_hourly_stats()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Maintenance error: {e}")
    
    async def _handle_unhealthy_worker(self, worker_id: str):
        """Handle an unhealthy worker."""
        async with self._lock:
            worker = self.workers.get(worker_id)
            if not worker:
                return
            
            # Reassign current task if any
            if worker.current_task and worker.current_task in self.processing:
                item = self.processing[worker.current_task]
                item.status = EvaluationStatus.QUEUED
                item.assigned_to = None
                self.queue.insert(0, item)  # Priority requeue
                del self.processing[worker.current_task]
            
            # Remove worker
            del self.workers[worker_id]
            
            # Cancel worker task
            if worker_id in self._worker_tasks:
                self._worker_tasks[worker_id].cancel()
                del self._worker_tasks[worker_id]
        
        await self._publish_update("worker_removed", {
            "worker_id": worker_id,
            "reason": "unhealthy"
        })


class QueueMetrics:
    """Tracks metrics for the evaluation queue."""
    
    def __init__(self):
        self.submissions_total = 0
        self.completions_total = 0
        self.failures_total = 0
        self.cancellations_total = 0
        self.total_wait_time = 0.0
        self.total_processing_time = 0.0
        self.hourly_stats: List[Dict[str, Any]] = []
        
    def record_submission(self, item: QueueItem):
        """Record a new submission."""
        self.submissions_total += 1
    
    def record_completion(self, item: QueueItem):
        """Record a completion."""
        self.completions_total += 1
        if item.wait_time:
            self.total_wait_time += item.wait_time.total_seconds()
        if item.processing_time:
            self.total_processing_time += item.processing_time.total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "submissions_total": self.submissions_total,
            "completions_total": self.completions_total,
            "failures_total": self.failures_total,
            "cancellations_total": self.cancellations_total,
            "average_wait_time": (
                self.total_wait_time / self.completions_total 
                if self.completions_total > 0 else 0
            ),
            "average_processing_time": (
                self.total_processing_time / self.completions_total
                if self.completions_total > 0 else 0
            ),
            "success_rate": (
                self.completions_total / self.submissions_total
                if self.submissions_total > 0 else 0
            )
        }
    
    def calculate_hourly_stats(self):
        """Calculate hourly statistics."""
        # In real implementation, track detailed hourly metrics
        pass