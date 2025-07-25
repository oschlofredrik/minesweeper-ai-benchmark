"""Error handling and retry logic for Vercel."""
import time
import json
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union
from http.server import BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TiltsError(Exception):
    """Base exception for Tilts platform."""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code

class APIError(TiltsError):
    """API-related errors."""
    pass

class GameError(TiltsError):
    """Game execution errors."""
    pass

class ModelError(TiltsError):
    """AI model errors."""
    pass

class DatabaseError(TiltsError):
    """Database operation errors."""
    pass

class ValidationError(TiltsError):
    """Input validation errors."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, error_code="VALIDATION_ERROR", status_code=400)
        self.field = field

class RateLimitError(TiltsError):
    """Rate limiting errors."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, error_code="RATE_LIMITED", status_code=429)
        self.retry_after = retry_after

class AuthenticationError(TiltsError):
    """Authentication errors."""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, error_code="AUTH_REQUIRED", status_code=401)

class AuthorizationError(TiltsError):
    """Authorization errors."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, error_code="FORBIDDEN", status_code=403)

def handle_errors(handler: BaseHTTPRequestHandler):
    """Decorator to handle errors in HTTP request handlers."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TiltsError as e:
                logger.error(f"Tilts error in {func.__name__}: {str(e)}")
                send_error_response(handler, e.status_code, {
                    "error": str(e),
                    "error_code": e.error_code,
                    "details": getattr(e, "details", None)
                })
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
                send_error_response(handler, 500, {
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "details": str(e) if handler.headers.get("X-Debug") else None
                })
        return wrapper
    return decorator

def send_error_response(handler: BaseHTTPRequestHandler, status_code: int, error_data: Dict[str, Any]):
    """Send a JSON error response."""
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Access-Control-Allow-Origin', '*')
    
    # Add retry-after header for rate limits
    if status_code == 429 and 'retry_after' in error_data:
        handler.send_header('Retry-After', str(error_data['retry_after']))
    
    handler.end_headers()
    handler.wfile.write(json.dumps(error_data).encode())

def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """Decorator to retry function calls on errors.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called before each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}")
            
            # Re-raise the last exception if all retries failed
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

class ErrorContext:
    """Context manager for error handling with cleanup."""
    def __init__(self, operation: str, cleanup: Optional[Callable] = None):
        self.operation = operation
        self.cleanup = cleanup
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error in {self.operation}: {exc_val}")
            
            if self.cleanup:
                try:
                    self.cleanup()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")
        
        # Don't suppress the exception
        return False

def validate_request_data(data: Dict[str, Any], required_fields: Dict[str, Type]) -> Dict[str, Any]:
    """Validate request data against required fields and types.
    
    Args:
        data: Request data to validate
        required_fields: Dict mapping field names to expected types
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    for field, expected_type in required_fields.items():
        if field not in data:
            raise ValidationError(f"Missing required field: {field}", field=field)
        
        value = data[field]
        
        # Handle None values
        if value is None and expected_type is not type(None):
            raise ValidationError(f"Field '{field}' cannot be null", field=field)
        
        # Type checking
        if value is not None and not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}",
                field=field
            )
        
        validated[field] = value
    
    return validated

class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.is_open:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                # Try to close the circuit
                self.is_open = False
                self.failure_count = 0
            else:
                raise TiltsError(
                    "Service temporarily unavailable",
                    error_code="CIRCUIT_OPEN",
                    status_code=503
                )
        
        try:
            result = func(*args, **kwargs)
            # Reset on success
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e

# Global circuit breakers for different services
model_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
database_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

def handle_model_error(error: Exception) -> ModelError:
    """Convert model-specific errors to ModelError."""
    error_str = str(error).lower()
    
    if "rate limit" in error_str:
        return RateLimitError("Model API rate limit exceeded", retry_after=60)
    elif "authentication" in error_str or "api key" in error_str:
        return AuthenticationError("Invalid API key")
    elif "timeout" in error_str:
        return ModelError("Model request timed out", error_code="TIMEOUT", status_code=504)
    elif "context length" in error_str or "token limit" in error_str:
        return ModelError("Context length exceeded", error_code="CONTEXT_TOO_LONG", status_code=400)
    else:
        return ModelError(f"Model error: {str(error)}", error_code="MODEL_ERROR")

def safe_json_parse(data: Union[str, bytes], default: Any = None) -> Any:
    """Safely parse JSON data with error handling."""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return default