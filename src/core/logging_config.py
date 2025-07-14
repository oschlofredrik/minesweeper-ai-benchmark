"""Logging configuration for the Tilts platform."""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import traceback


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "game_id"):
            log_data["game_id"] = record.game_id
        if hasattr(record, "model"):
            log_data["model"] = record.model
        if hasattr(record, "model_name"):
            log_data["model_name"] = record.model_name
        if hasattr(record, "model_provider"):
            log_data["model_provider"] = record.model_provider
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "game_num"):
            log_data["game_num"] = record.game_num
        if hasattr(record, "move_num"):
            log_data["move_num"] = record.move_num
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        record.timestamp = timestamp
        
        # Custom format
        if record.exc_info:
            exc_text = '\n'.join(traceback.format_exception(*record.exc_info))
            return f"[{record.timestamp}] {record.levelname} [{record.name}] {record.getMessage()}\n{exc_text}"
        else:
            return f"[{record.timestamp}] {record.levelname} [{record.name}] {record.getMessage()}"


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "data/logs/tilts_benchmark.log",
    enable_console: bool = True,
    enable_file: bool = True,
    structured: bool = True
) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_console: Enable console logging
        enable_file: Enable file logging
        structured: Use structured JSON logging for files
    """
    # Create logs directory if it doesn't exist
    if enable_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(ColoredFormatter())
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        root_logger.addHandler(file_handler)
    
    # Create specific loggers
    loggers = {
        "evaluation": logging.getLogger("evaluation"),
        "api": logging.getLogger("api"),
        "models": logging.getLogger("models"),
        "tasks": logging.getLogger("tasks"),
        "games": logging.getLogger("games"),
    }
    
    # Log startup
    root_logger.info(
        "Logging initialized",
        extra={
            "log_level": log_level,
            "log_file": log_file if enable_file else None,
            "console": enable_console,
            "structured": structured
        }
    )
    
    return loggers


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def log_evaluation_start(logger: logging.Logger, job_id: str, model: str, num_games: int):
    """Log evaluation start."""
    logger.info(
        f"Starting evaluation job",
        extra={
            "job_id": job_id,
            "model": model,
            "num_games": num_games,
            "event": "evaluation_start"
        }
    )


def log_evaluation_progress(logger: logging.Logger, job_id: str, current: int, total: int):
    """Log evaluation progress."""
    logger.debug(
        f"Evaluation progress: {current}/{total}",
        extra={
            "job_id": job_id,
            "progress": current / total,
            "current": current,
            "total": total,
            "event": "evaluation_progress"
        }
    )


def log_evaluation_complete(logger: logging.Logger, job_id: str, duration: float, results: Dict[str, Any]):
    """Log evaluation completion."""
    logger.info(
        f"Evaluation completed successfully",
        extra={
            "job_id": job_id,
            "duration": duration,
            "win_rate": results.get("metrics", {}).get("win_rate"),
            "event": "evaluation_complete"
        }
    )


def log_evaluation_error(logger: logging.Logger, job_id: str, error: Exception):
    """Log evaluation error."""
    logger.error(
        f"Evaluation failed: {str(error)}",
        extra={
            "job_id": job_id,
            "error_type": type(error).__name__,
            "event": "evaluation_error"
        },
        exc_info=True
    )


def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, duration: float):
    """Log API request."""
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "event": "api_request"
        }
    )


def log_model_error(logger: logging.Logger, model: str, error: Exception, context: Dict[str, Any] = None):
    """Log model-specific error."""
    logger.error(
        f"Model error for {model}: {str(error)}",
        extra={
            "model": model,
            "error_type": type(error).__name__,
            "context": context or {},
            "event": "model_error"
        },
        exc_info=True
    )