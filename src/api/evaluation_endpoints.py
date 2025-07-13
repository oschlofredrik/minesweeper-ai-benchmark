"""API endpoints for running evaluations from the web interface."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
import json
import time
import traceback

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from src.core.config import settings
from src.core.logging_config import (
    get_logger, 
    log_evaluation_start, 
    log_evaluation_progress,
    log_evaluation_complete, 
    log_evaluation_error,
    LogContext
)
from src.core.types import Difficulty
from src.evaluation import EvaluationEngine
from src.tasks import TaskRepository, TaskGenerator
from src.models import create_model, ModelConfig

# Initialize logger
logger = get_logger("api.evaluation")


router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class TaskGenerationRequest(BaseModel):
    """Request to generate benchmark tasks."""
    num_tasks: int = 10
    difficulty: Optional[str] = None
    task_type: Optional[str] = None


class TaskGenerationResponse(BaseModel):
    """Response from task generation."""
    job_id: str
    status: str
    num_tasks: int
    message: str


class EvaluationJobRequest(BaseModel):
    """Request to start an evaluation job."""
    model_name: str
    model_provider: str  # "openai" or "anthropic"
    num_games: int = 10
    task_type: Optional[str] = None
    difficulty: Optional[str] = None
    api_key: Optional[str] = None  # Optional, can use env vars


class EvaluationJobResponse(BaseModel):
    """Response from starting an evaluation."""
    job_id: str
    status: str
    model: str
    num_games: int
    message: str


class JobStatus(BaseModel):
    """Status of an evaluation job."""
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results_file: Optional[str] = None


# In-memory job tracking (in production, use Redis or database)
jobs: Dict[str, JobStatus] = {}


@router.post("/generate-tasks", response_model=TaskGenerationResponse)
async def generate_tasks(
    request: TaskGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate new benchmark tasks."""
    job_id = f"task_gen_{uuid4().hex[:8]}"
    
    logger.info(
        f"Task generation requested",
        extra={
            "job_id": job_id,
            "num_tasks": request.num_tasks,
            "difficulty": request.difficulty,
            "task_type": request.task_type
        }
    )
    
    # Create job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message=f"Generating {request.num_tasks} tasks...",
        started_at=datetime.utcnow()
    )
    
    # Run task generation in background
    background_tasks.add_task(
        run_task_generation,
        job_id,
        request.num_tasks,
        request.difficulty,
        request.task_type
    )
    
    return TaskGenerationResponse(
        job_id=job_id,
        status="started",
        num_tasks=request.num_tasks,
        message="Task generation started. Check job status for progress."
    )


@router.post("/start", response_model=EvaluationJobResponse)
async def start_evaluation(
    request: EvaluationJobRequest,
    background_tasks: BackgroundTasks
):
    """Start a new evaluation job."""
    job_id = f"eval_{uuid4().hex[:8]}"
    
    # Validate model
    if request.model_provider not in ["openai", "anthropic"]:
        logger.warning(
            f"Invalid model provider requested",
            extra={
                "provider": request.model_provider,
                "job_id": job_id
            }
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid model provider. Must be 'openai' or 'anthropic'"
        )
    
    logger.info(
        f"Evaluation job requested",
        extra={
            "job_id": job_id,
            "model": request.model_name,
            "provider": request.model_provider,
            "num_games": request.num_games,
            "task_type": request.task_type,
            "difficulty": request.difficulty,
            "has_api_key": bool(request.api_key)
        }
    )
    
    # Create job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message=f"Starting evaluation of {request.model_name}...",
        started_at=datetime.utcnow()
    )
    
    # Run evaluation in background
    background_tasks.add_task(
        run_evaluation_job,
        job_id,
        request.model_name,
        request.model_provider,
        request.num_games,
        request.task_type,
        request.difficulty,
        request.api_key
    )
    
    return EvaluationJobResponse(
        job_id=job_id,
        status="started",
        model=request.model_name,
        num_games=request.num_games,
        message="Evaluation started. Check job status for progress."
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of an evaluation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@router.get("/jobs", response_model=List[JobStatus])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Number of jobs to return")
):
    """List all evaluation jobs."""
    job_list = list(jobs.values())
    
    # Filter by status if provided
    if status:
        job_list = [j for j in job_list if j.status == status]
    
    # Sort by started_at descending
    job_list.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
    
    return job_list[:limit]


async def run_task_generation(
    job_id: str,
    num_tasks: int,
    difficulty: Optional[str],
    task_type: Optional[str]
):
    """Background task to generate benchmark tasks."""
    start_time = time.time()
    
    with LogContext(logger, job_id=job_id):
        try:
            logger.info(f"Starting task generation")
            jobs[job_id].status = "running"
            jobs[job_id].message = "Generating tasks..."
            
            # Create task generator
            generator = TaskGenerator()
            repository = TaskRepository()
            
            # Generate tasks
            generated = 0
            errors = 0
            
            for i in range(num_tasks):
                try:
                    # Update progress
                    jobs[job_id].progress = i / num_tasks
                    
                    # Convert string difficulty to enum if provided
                    diff_enum = Difficulty.EXPERT  # default
                    if difficulty:
                        try:
                            diff_enum = Difficulty(difficulty.lower())
                        except ValueError:
                            logger.warning(f"Invalid difficulty '{difficulty}', using EXPERT")
                    
                    # Generate task
                    if task_type == "static":
                        task = generator.generate_static_task(difficulty=diff_enum)
                    else:
                        task = generator.generate_interactive_task(difficulty=diff_enum)
                    
                    # Save task
                    repository.save_task(task)
                    generated += 1
                    
                    # Log progress every 10%
                    if i % max(1, num_tasks // 10) == 0:
                        logger.debug(
                            f"Task generation progress",
                            extra={
                                "progress": i / num_tasks,
                                "generated": generated,
                                "errors": errors
                            }
                        )
                        
                except Exception as task_error:
                    errors += 1
                    logger.warning(
                        f"Failed to generate task {i}",
                        extra={"error": str(task_error)},
                        exc_info=True
                    )
            
            # Complete
            duration = time.time() - start_time
            jobs[job_id].status = "completed"
            jobs[job_id].progress = 1.0
            jobs[job_id].message = f"Successfully generated {generated} tasks"
            jobs[job_id].completed_at = datetime.utcnow()
            
            logger.info(
                f"Task generation completed",
                extra={
                    "duration": duration,
                    "generated": generated,
                    "errors": errors,
                    "success_rate": generated / num_tasks if num_tasks > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            jobs[job_id].status = "failed"
            jobs[job_id].message = f"Error: {str(e)}"
            jobs[job_id].completed_at = datetime.utcnow()
            
            logger.error(
                f"Task generation failed",
                extra={
                    "duration": duration,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )


async def run_evaluation_job(
    job_id: str,
    model_name: str,
    model_provider: str,
    num_games: int,
    task_type: Optional[str],
    difficulty: Optional[str],
    api_key: Optional[str]
):
    """Background task to run evaluation."""
    start_time = time.time()
    
    with LogContext(logger, job_id=job_id, model=model_name):
        try:
            log_evaluation_start(logger, job_id, model_name, num_games)
            jobs[job_id].status = "running"
            jobs[job_id].message = f"Evaluating {model_name}..."
            
            # Create model config
            logger.debug(
                f"Creating model configuration",
                extra={
                    "provider": model_provider,
                    "model_id": model_name,
                    "has_custom_key": bool(api_key)
                }
            )
            
            model_config = ModelConfig(
                name=model_name,
                provider=model_provider,
                model_id=model_name,
                temperature=0.7,
                max_tokens=1000,
                additional_params={}
            )
            
            # Add API key if provided
            if api_key:
                model_config.additional_params["api_key"] = api_key
            
            # Create model
            try:
                model = create_model(model_config)
                logger.debug(f"Model created successfully")
            except Exception as model_error:
                logger.error(
                    f"Failed to create model",
                    extra={"error_type": type(model_error).__name__},
                    exc_info=True
                )
                raise
            
            # Generate tasks for evaluation
            logger.info(f"Generating tasks for evaluation")
            generator = TaskGenerator()
            repository = TaskRepository()
            
            tasks = []
            for i in range(num_games):
                try:
                    # Convert difficulty
                    diff_enum = Difficulty.EXPERT
                    if difficulty:
                        try:
                            diff_enum = Difficulty(difficulty.lower())
                        except ValueError:
                            pass
                    
                    # Generate task
                    if task_type == "static":
                        task = generator.generate_static_task(difficulty=diff_enum)
                    elif task_type == "interactive":
                        task = generator.generate_interactive_task(difficulty=diff_enum)
                    else:
                        # Mix of both
                        task = (generator.generate_static_task(difficulty=diff_enum) 
                                if i % 2 == 0 else 
                                generator.generate_interactive_task(difficulty=diff_enum))
                    
                    repository.save_task(task)
                    tasks.append(task)
                    
                    # Update progress
                    jobs[job_id].progress = (i + 1) / num_games * 0.3  # First 30% for generation
                    jobs[job_id].message = f"Generated {i + 1}/{num_games} tasks..."
                    
                except Exception as task_error:
                    logger.warning(f"Failed to generate task {i}: {str(task_error)}")
            
            if not tasks:
                raise Exception("Failed to generate any tasks")
            
            logger.info(f"Generated {len(tasks)} tasks, starting evaluation")
            
            # Create evaluation engine
            engine = EvaluationEngine()
            
            # Update status
            jobs[job_id].message = f"Evaluating {model_name} on {len(tasks)} games..."
            
            # Run evaluation
            logger.info(f"Starting evaluation run")
            results = await engine.evaluate_model(
                model_config=model_config,
                tasks=tasks,
                prompt_format="standard",
                verbose=False
            )
            
            # Update progress
            jobs[job_id].progress = 1.0
            jobs[job_id].message = f"Completed {len(tasks)} games"
            
            # Log evaluation metrics
            metrics = results.get("metrics", {})
            logger.info(
                f"Evaluation metrics computed",
                extra={
                    "win_rate": metrics.get("win_rate"),
                    "accuracy": metrics.get("accuracy"),
                    "valid_move_rate": metrics.get("valid_move_rate"),
                    "global_score": metrics.get("global_score")
                }
            )
            
            # Save results
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"{model_name}_{timestamp}_summary.json"
            results_path = Path("data/results") / results_file
            
            # Ensure results directory exists
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
                
            logger.debug(f"Results saved to {results_file}")
            
            # Complete
            duration = time.time() - start_time
            jobs[job_id].status = "completed"
            jobs[job_id].progress = 1.0
            jobs[job_id].message = f"Evaluation completed successfully"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].results_file = results_file
            
            log_evaluation_complete(logger, job_id, duration, results)
            
        except Exception as e:
            duration = time.time() - start_time
            jobs[job_id].status = "failed"
            jobs[job_id].message = f"Error: {str(e)}"
            jobs[job_id].completed_at = datetime.utcnow()
            
            log_evaluation_error(logger, job_id, e)
            
            # Add additional debugging info
            logger.error(
                f"Evaluation job failed after {duration:.2f} seconds",
                extra={
                    "duration": duration,
                    "error_type": type(e).__name__,
                    "error_details": traceback.format_exc()
                }
            )


@router.get("/available-models")
async def get_available_models():
    """Get list of available models for evaluation."""
    return {
        "openai": [
            {"id": "gpt-4", "name": "GPT-4", "description": "Most capable OpenAI model"},
            {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo", "description": "Faster GPT-4 variant"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and cost-effective"},
        ],
        "anthropic": [
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Most capable Claude model"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "Balanced performance"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "description": "Fast and efficient"},
        ]
    }